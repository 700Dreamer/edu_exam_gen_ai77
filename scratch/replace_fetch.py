import re

file_path = r"c:\Users\Ki\Desktop\kizito\eduquestai\eduquest_2_stabler2_new\sys\src\frontend\app\page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace "fetch(" with "authFetch("
# We will do it carefully using regex. We can match any 'fetch(' that is not prefixed with 'window.' or 'const auth' or 'async auth' or 'function auth'
# Or we can just do a simple regex replace and then check.
# Let's use a regex that looks for 'fetch(' as a word boundary
new_content = re.sub(r'\bfetch\(', 'authFetch(', content)

# But wait, we want to make sure if we write our authFetch utility, it uses window.fetch or similar.
# Let's search if there's any place where 'fetch' is used as a variable name or in comments.
# In page.tsx:
# Line 536: const fetchLibrary = async () => { ... } -> this does NOT end in '(' (except as a function call elsewhere, e.g. fetchLibrary())
# So re.sub(r'\bfetch\(', ...) is perfect because it only matches 'fetch' followed by '('.

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Replacement of fetch( with authFetch( complete.")
