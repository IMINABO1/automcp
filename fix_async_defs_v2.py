
import re
import os

FILE_PATH = "generated_tools.py"

if not os.path.exists(FILE_PATH):
    print(f"Error: {FILE_PATH} not found.")
    exit(1)

with open(FILE_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
modified_count = 0

for line in lines:
    # Check if the line is a function definition and doesn't already have 'async'
    if line.strip().startswith("def ") and "async def" not in line:
        new_line = line.replace("def ", "async def ", 1)
        new_lines.append(new_line)
        modified_count += 1
    else:
        new_lines.append(line)

if modified_count > 0:
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Successfully converted {modified_count} functions to 'async def'")
else:
    print("No functions needing conversion found.")
