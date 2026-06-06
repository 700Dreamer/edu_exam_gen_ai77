import asyncio
import os
import sys
import uuid
import httpx
from fastapi import status

# Set up project path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from server import app
from core.models import create_db_and_tables, async_session_maker, User, AuditLog
from sqlalchemy import select, delete

async def clean_database():
    """Clean user and audit_log tables before test."""
    async with async_session_maker() as session:
        await session.execute(delete(AuditLog))
        await session.execute(delete(User))
        await session.commit()

async def test_flow():
    # 1. Initialize and clean database
    await create_db_and_tables()
    await clean_database()
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n--- Test Phase 1: User Registration ---")
        
        # Register Teacher
        staff_payload = {
            "email": "staff@eduquest.com",
            "password": "SecurePassword123!",
            "role": "staff"
        }
        res = await client.post("/api/auth/register", json=staff_payload)
        assert res.status_code == status.HTTP_201_CREATED, f"Teacher registration failed: {res.text}"
        staff_data = res.json()
        print("Staff registered:", staff_data["email"], "ID:", staff_data["id"])
        
        
        
        # Register Admin
        admin_payload = {
            "email": "admin@eduquest.com",
            "password": "SecurePassword123!",
            "role": "admin"
        }
        res = await client.post("/api/auth/register", json=admin_payload)
        assert res.status_code == status.HTTP_201_CREATED
        admin_data = res.json()
        print("Admin registered:", admin_data["email"], "ID:", admin_data["id"])
        
        print("\n--- Test Phase 2: Login and JWT Strategy ---")
        
        # Login Staff
        res = await client.post("/api/auth/jwt/login", data={
            "username": "staff@eduquest.com",
            "password": "SecurePassword123!"
        })
        assert res.status_code == status.HTTP_200_OK
        staff_token = res.json()["access_token"]
        print("Staff logged in successfully. Token acquired.")
        
        
        
        # Login Admin
        res = await client.post("/api/auth/jwt/login", data={
            "username": "admin@eduquest.com",
            "password": "SecurePassword123!"
        })
        assert res.status_code == status.HTTP_200_OK
        admin_token = res.json()["access_token"]
        print("Admin logged in successfully. Token acquired.")
        
        print("\n--- Test Phase 3: Role-Based Authorization Restrictions ---")
        
        # Generate payload
        payload = {
            "mode": "Exams",
            "subject": "Mathematics",
            "level": "Primary 7",
            "term": "Term 1",
            "question_count": 2,
            "ai_model": "gpt-4o",
            "topic": ""
        }
        
        # Request without token (Guest)
        print("Testing guest access to /api/generate (should be 401 Unauthorized)...")
        res = await client.post("/api/generate", json=payload)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        print("Guest access rejected correctly.")
        
        
        
        # Request with Teacher token (Teacher - should succeed)
        print("Testing staff access to /api/generate (mocking generate_ai_content for test)...")
        # To avoid calling OpenAI APIs during unit testing, we pass content_override
        payload["content_override"] = json.dumps({"questions": [{"number": 1, "type": "multiple_choice", "instruction": "Solve 1+1", "content": {}}]})
        res = await client.post("/api/generate", json=payload, headers={"Authorization": f"Bearer {staff_token}"})
        assert res.status_code == status.HTTP_200_OK
        print("Staff generation request succeeded.")
        
        print("\n--- Test Phase 4: Audit Logging and Activity Monitoring ---")
        
        
        
        # Query audit logs as admin (should succeed)
        print("Testing admin access to /api/admin/audit-logs (should succeed)...")
        res = await client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == status.HTTP_200_OK
        logs_data = res.json()["logs"]
        print(f"Admin retrieved {len(logs_data)} audit log entries:")
        for log in logs_data:
            print(f" - [{log['timestamp']}] User: {log['user_email']} | Action: {log['action']} | Details: {log['details']}")
            
        # Verify the "generate_exam" action is logged with teacher's email
        actions = [l["action"] for l in logs_data]
        emails = [l["user_email"] for l in logs_data]
        assert "generate_exam" in actions, "generate_exam not found in audit log"
        assert "staff@eduquest.com" in emails, "teacher email not found in audit log"
        
        print("\nVerification successful: All auth and logging checks passed.")

if __name__ == "__main__":
    import json
    asyncio.run(test_flow())
