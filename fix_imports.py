
import os
import re

FILE_PATH = "generated_tools.py"

if not os.path.exists(FILE_PATH):
    print(f"Error: {FILE_PATH} not found.")
    exit(1)

with open(FILE_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
modified_count = 0

for line in lines:
    stripped = line.strip()
    
    # 1. Comment out invalid imports
    if stripped.startswith("from fastmcp.mcp import") or \
       stripped.startswith("from fastmcp.exceptions import") or \
       stripped.startswith("from mcp.tool import") or \
       stripped.startswith("from loguru import"):
        new_lines.append(f"# {line}")
        modified_count += 1
        continue

    # 2. Fix decorators
    if stripped == "@Tool()":
        new_lines.append(line.replace("@Tool()", "@mcp.tool()"))
        modified_count += 1
        continue
        
    if stripped == "@tool()":
        new_lines.append(line.replace("@tool()", "@mcp.tool()"))
        modified_count += 1
        continue

    new_lines.append(line)

if modified_count > 0:
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Successfully fixed {modified_count} imports and decorators in generated_tools.py")
else:
    print("No necessary changes found.")
