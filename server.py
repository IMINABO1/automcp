from mcp.server.fastmcp import FastMCP
import config
import os
import sys

# Initialize FastMCP
mcp = FastMCP("AutoMCP")

# Global context for exec
# We need to make sure 'mcp' is available to the executed code so @mcp.tool() works
execution_context = {
    "mcp": mcp,
    "httpx": None # Will be imported in generated code, but good to have
}

@mcp.tool()
def reload_tools():
    """Reloads the generated tools from the generated_tools.py file."""
    try:
        if not os.path.exists(config.GENERATED_TOOLS_FILE):
            return "No generated tools file found."
            
        with open(config.GENERATED_TOOLS_FILE, "r") as f:
            code = f.read()
        
        # Execute the code. 
        # The code is expected to contain @mcp.tool() calls which register tools to the 'mcp' object.
        # We pass our existing 'mcp' instance in the globals.
        
        global execution_context
        # Update execution context with necessary imports if needed
        import httpx
        execution_context["httpx"] = httpx
        
        exec(code, execution_context)
        return "Tools reloaded successfully!"
    except Exception as e:
        return f"Error reloading tools: {str(e)}"

# Attempt initial load
sys.stderr.write("Attempting initial tool load...\n")
reload_tools()

if __name__ == "__main__":
    sys.stderr.write("Starting AutoMCP Server...\n")
    mcp.run()
