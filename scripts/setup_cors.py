import os
import sys

# Add project root to Python path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.storage import get_s3_client, S3_BUCKET_NAME
from botocore.exceptions import ClientError

def setup_cors():
    client = get_s3_client()
    
    cors_configuration = {
        'CORSRules': [{
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['PUT', 'POST', 'GET', 'HEAD', 'DELETE'],
            'AllowedOrigins': ['*'], # In production, restrict to edulytics.net
            'ExposeHeaders': ['ETag'],
            'MaxAgeSeconds': 3600
        }]
    }
    
    try:
        print(f"Setting CORS on bucket {S3_BUCKET_NAME}...")
        client.put_bucket_cors(
            Bucket=S3_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )
        print("CORS configuration applied successfully.")
    except ClientError as e:
        print(f"Failed to set CORS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_cors()
