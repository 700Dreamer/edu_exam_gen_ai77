import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_REGION = os.getenv("S3_REGION", "auto")

def get_s3_client():
    """Initializes and returns a boto3 S3 client configured for the Railway bucket."""
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION,
        config=Config(signature_version="s3v4")
    )

def generate_presigned_upload_urls(batch_id: str, filenames: List[str], expires_in: int = 7200) -> List[Dict[str, str]]:
    """
    Generates pre-signed URLs for uploading files directly from the browser to the S3 bucket.
    Expires in 2 hours (7200 seconds) by default to accommodate slow connections on large batches.
    """
    s3_client = get_s3_client()
    urls = []
    
    for filename in filenames:
        # Create a unique key in the bucket for this file
        key = f"batches/{batch_id}/{filename}"
        
        try:
            url = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": S3_BUCKET_NAME,
                    "Key": key,
                    # We don't enforce ContentType here strictly to avoid mismatch with browser,
                    # but if needed we can set ContentType="image/jpeg" etc.
                },
                ExpiresIn=expires_in
            )
            urls.append({
                "filename": filename,
                "key": key,
                "url": url
            })
        except ClientError as e:
            print(f"Error generating presigned URL for {filename}: {e}")
            raise
            
    return urls

def verify_objects_exist(keys: List[str]) -> bool:
    """Verifies that the given keys actually exist in the bucket and have > 0 bytes."""
    s3_client = get_s3_client()
    for key in keys:
        try:
            response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=key)
            if response.get("ContentLength", 0) == 0:
                print(f"Warning: Object {key} exists but is 0 bytes.")
                return False
        except ClientError as e:
            # If a 404 is thrown, the object does not exist.
            if e.response["Error"]["Code"] == "404":
                print(f"Verification failed: Object {key} does not exist.")
                return False
            raise
    return True

def generate_presigned_download_url(key: str, expires_in: int = 3600) -> str:
    """
    Generates a pre-signed URL for downloading/reading a file from the bucket.
    Used by the backend workers to read images during grading.
    """
    # If the key is just a local URL (e.g. from older batches), return it directly
    if not key.startswith("batches/"):
        return key

    s3_client = get_s3_client()
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": key
            },
            ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        print(f"Error generating download URL for {key}: {e}")
        raise
