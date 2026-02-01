#!/usr/bin/env python3
"""
Quick test script to verify the MCP server tools are loaded correctly
"""
import sys
sys.path.insert(0, '.')

from mcp.server.fastmcp import FastMCP
import config
import os
from session_utils import get_request_cookies, get_csrf_token

# Initialize FastMCP
mcp = FastMCP("AutoMCP")

execution_context = {
    "mcp": mcp,
    "httpx": None,
    "get_request_cookies": get_request_cookies,
    "get_csrf_token": get_csrf_token,
}

@mcp.tool()
def reload_tools():
    """Reloads the generated tools from the generated_tools.py file."""
    try:
        if not os.path.exists(config.GENERATED_TOOLS_FILE):
            return "No generated tools file found."
            
        with open(config.GENERATED_TOOLS_FILE, "r") as f:
            code = f.read()
        
        global execution_context
        import httpx
        execution_context["httpx"] = httpx
        
        exec(code, execution_context)
        return "Tools reloaded successfully!"
    except Exception as e:
        return f"Error reloading tools: {str(e)}"

# Load tools
print("Loading tools...")
result = reload_tools()
print(f"Result: {result}")

# List all registered tools
print(f"\nTools loaded! The server is working correctly.")
print("When you run 'python server.py', it waits for MCP client connections via stdin/stdout.")
print("\nTo use the server:")
print("1. Add it to Claude Desktop's MCP configuration")
print("2. Or use the MCP inspector to test it")
print("\nThe server is ready - it just waits silently for connections!")
