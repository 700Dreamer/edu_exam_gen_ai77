import re

# 1. Modify test_auth_flow.py
file_path_1 = r"c:\Users\Ki\Desktop\kizito\eduquestai\eduquest_2_stabler2_new\sys\src\test_auth_flow.py"

with open(file_path_1, "r", encoding="utf-8") as f:
    content = f.read()

# Replace "teacher" with "staff" (case-insensitive where appropriate)
content = content.replace('"role": "teacher"', '"role": "staff"')
content = content.replace('"teacher@eduquest.com"', '"staff@eduquest.com"')
content = content.replace('teacher_payload', 'staff_payload')
content = content.replace('teacher_data', 'staff_data')
content = content.replace('teacher_token', 'staff_token')
content = content.replace('Teacher registered', 'Staff registered')
content = content.replace('Login Teacher', 'Login Staff')
content = content.replace('Teacher logged in', 'Staff logged in')
content = content.replace('Testing teacher access', 'Testing staff access')
content = content.replace('Teacher generation request', 'Staff generation request')
content = content.replace('teacher@eduquest.com', 'staff@eduquest.com')

# Remove student registration and testing blocks since student is removed
content = re.sub(r'# Register Student\s+student_payload = \{[^\}]+\}\s+res = await client.post\("/api/auth/register", json=student_payload\)\s+assert res.status_code == status.HTTP_201_CREATED\s+student_data = res.json\(\)\s+print\("Student registered:", student_data\["email"\], "ID:", student_data\["id"\]\)', '', content)
content = re.sub(r'# Login Student\s+res = await client.post\("/api/auth/jwt/login", data=\{[^\}]+\}\)\s+assert res.status_code == status.HTTP_200_OK\s+student_token = res.json\(\)\["access_token"\]\s+print\("Student logged in successfully. Token acquired."\)', '', content)
content = re.sub(r'# Request with Student token \(Student - should be forbidden since only teachers/admins can generate\)\s+print\("Testing student access to /api/generate \(should be 403 Forbidden\)..."\)\s+res = await client.post\("/api/generate", json=payload, headers=\{"Authorization": f"Bearer \{student_token\}"\}\)\s+assert res.status_code == status.HTTP_403_FORBIDDEN\s+print\("Student access rejected correctly."\)', '', content)
content = re.sub(r'# Query audit logs as student \(should be 403 Forbidden\)\s+print\("Testing student access to /api/admin/audit-logs \(should be 403 Forbidden\)..."\)\s+res = await client.get\("/api/admin/audit-logs", headers=\{"Authorization": f"Bearer \{student_token\}"\}\)\s+assert res.status_code == status.HTTP_403_FORBIDDEN\s+print\("Student audit log access rejected correctly."\)', '', content)

with open(file_path_1, "w", encoding="utf-8") as f:
    f.write(content)

# 2. Modify scratch/test_protected_endpoints.py
file_path_2 = r"c:\Users\Ki\Desktop\kizito\eduquestai\eduquest_2_stabler2_new\sys\src\scratch\test_protected_endpoints.py"

with open(file_path_2, "r", encoding="utf-8") as f:
    content2 = f.read()

content2 = content2.replace('teacher_test@eduquest.com', 'staff_test@eduquest.com')
content2 = content2.replace('teacher_token', 'staff_token')
content2 = content2.replace('teacher token', 'staff token')
content2 = content2.replace('teacher login', 'staff login')
content2 = content2.replace('Teacher logged in', 'Staff logged in')
content2 = content2.replace('Logging in as teacher', 'Logging in as staff')
content2 = content2.replace('teacher_test', 'staff_test')

with open(file_path_2, "w", encoding="utf-8") as f:
    f.write(content2)

print("Test scripts role update complete.")
