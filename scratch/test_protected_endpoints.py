import httpx
import json

def test_protected():
    base_url = "http://127.0.0.1:8000"
    print("\n--- Direct Server Authentication and Permission Test ---")
    
    # Use a client with a 30-second timeout to avoid any quick timeouts during PDF generation
    with httpx.Client(timeout=30.0) as client:
        # 1. Login as the teacher we registered
        print("1. Logging in as staff...")
        res = client.post(f"{base_url}/api/auth/jwt/login", data={
            "username": "staff_test@eduquest.com",
            "password": "SecurePassword123!"
        })
        if res.status_code != 200:
            print("Teacher login failed:", res.text)
            return
        staff_token = res.json()["access_token"]
        print("Staff logged in successfully. Token acquired.")
        
        # 2. Test teacher accessing admin audit logs (should be 403 Forbidden)
        print("\n2. Querying admin audit-logs with staff token...")
        res = client.get(f"{base_url}/api/admin/audit-logs", headers={"Authorization": f"Bearer {staff_token}"})
        print("Status Code (should be 403):", res.status_code)
        print("Detail:", res.json())
        assert res.status_code == 403
        
        # 3. Call generate endpoint with staff token (should succeed)
        print("\n3. Testing exam generation with staff token...")
        payload = {
            "mode": "Exams",
            "subject": "Mathematics",
            "level": "Primary 7",
            "term": "Term 1",
            "question_count": 1,
            "content_override": json.dumps({"questions": [{"number": 1, "type": "multiple_choice", "instruction": "Solve 1+1", "content": {}}]})
        }
        res = client.post(f"{base_url}/api/generate", json=payload, headers={"Authorization": f"Bearer {staff_token}"})
        print("Status Code (should be 200):", res.status_code)
        print("Response keys:", list(res.json().keys()))
        assert res.status_code == 200
        
        # 4. Register Admin (if not already registered)
        print("\n4. Registering admin user...")
        admin_payload = {
            "email": "admin_test@eduquest.com",
            "password": "SecurePassword123!",
            "role": "admin"
        }
        res = client.post(f"{base_url}/api/auth/register", json=admin_payload)
        print("Admin registration Status Code:", res.status_code)
        # Note: 400 Bad Request is fine if the user is already registered from previous run
        assert res.status_code in [201, 400]
        
        # 5. Login Admin
        print("Logging in as admin...")
        res = client.post(f"{base_url}/api/auth/jwt/login", data={
            "username": "admin_test@eduquest.com",
            "password": "SecurePassword123!"
        })
        if res.status_code != 200:
             print("Admin login failed:", res.text)
             return
        admin_token = res.json()["access_token"]
        print("Admin logged in successfully.")
        
        # 6. Retrieve Audit Logs as Admin
        print("\n6. Retrieving audit logs with admin token...")
        res = client.get(f"{base_url}/api/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
        print("Status Code (should be 200):", res.status_code)
        logs = res.json()["logs"]
        print(f"Retrieved {len(logs)} audit log entries:")
        for log in logs:
             print(f" - [{log['timestamp']}] User: {log['user_email']} | Action: {log['action']} | Details: {log['details']}")
             
        # Check that logs contain register, login, and generate_exam actions
        actions = [l["action"] for l in logs]
        print("\nActions logged in Audit Database:", actions)
        assert "generate_exam" in actions
        assert "login" in actions
        assert "register" in actions
        print("\nSUCCESS: All endpoint role checks and activity logging verified successfully!")

if __name__ == "__main__":
    test_protected()
