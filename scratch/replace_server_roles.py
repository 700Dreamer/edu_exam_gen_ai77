file_path = r"c:\Users\Ki\Desktop\kizito\eduquestai\eduquest_2_stabler2_new\sys\src\server.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace require_role(["teacher", "admin"]) with require_role(["staff", "admin"])
new_content = content.replace('require_role(["teacher", "admin"])', 'require_role(["staff", "admin"])')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Replacement in server.py complete.")
