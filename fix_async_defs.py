
import re
import os

FILE_PATH = "generated_tools.py"

if not os.path.exists(FILE_PATH):
    print(f"Error: {FILE_PATH} not found.")
    exit(1)

with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Replace 'def function_name(' with 'async def function_name('
# We assume all tools in this file are intended to be async since they use httpx.AsyncClient
# We use a negative lookbehind to ensure we don't double-patch (async async def)
new_content = re.sub(r'(?<!async )def ([a-zA-Z_]\w*)\(', r'async def \1(', content)

# Check if changes were made
if content != new_content:
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully converted functions to 'async def' in generated_tools.py")
else:
    print("No functions needing conversion found.")
