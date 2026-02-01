
import re
import os

FILE_PATH = "generated_tools.py"

if not os.path.exists(FILE_PATH):
    print(f"Error: {FILE_PATH} not found.")
    exit(1)

with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Ensure 'from typing import Any' exists
if "from typing import Any" not in content:
    # Insert it after the first import or at the top
    if "import " in content:
        content = re.sub(r'^(import .*)$', r'from typing import Any\n\1', content, count=1, flags=re.MULTILINE)
    else:
        content = "from typing import Any\n" + content

# 2. Replace ': any' with ': Any'
# We use regex to match ': any' followed by , or ) or newline, to avoid matching 'any' in variable names if possible,
# though 'any' is a keyword/builtin so it shouldn't be a variable name ideally, but in generated code who knows.
# The error said "built-in function any", so it's definitely just "any".
# Matches ": any" with word boundaries or specific follow chars.
# A safe bet is replacing ": any" when it's likely a type hint.
content = re.sub(r':\s*any\b', ': Any', content)
content = re.sub(r'->\s*any\b', '-> Any', content)

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully replaced 'any' type hints with 'Any' and added import.")
