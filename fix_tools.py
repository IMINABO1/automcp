
import os

FILE_PATH = "generated_tools.py"

if not os.path.exists(FILE_PATH):
    print(f"Error: {FILE_PATH} not found.")
    exit(1)

with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the invalid f-string conversion
# Replacing {e.request.url!url} with {e.request.url}
new_content = content.replace("!url}", "}")

if content != new_content:
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully patched generated_tools.py")
else:
    print("No occurrences of '!url}' found.")
