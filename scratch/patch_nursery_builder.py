import re

with open('ui/nursery_builder.py', 'r') as f:
    code = f.read()

# Replace: items = content.get("items", [])
# With: items = (content.get("items") or [])
# And: numbers = content.get("numbers", [1, 2, 3])
# With: numbers = (content.get("numbers") or [1, 2, 3])

# The regex matches: content.get("something", [something])
pattern = r'content\.get\("([^"]+)",\s*(\[[^\]]*\])\)'
replacement = r'(content.get("\1") or \2)'

new_code = re.sub(pattern, replacement, code)

with open('ui/nursery_builder.py', 'w') as f:
    f.write(new_code)

print("Patch applied.")
