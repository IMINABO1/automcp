from google import genai
import json
import os
import config

# Configure Gemini
if not config.GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in environment.")

client = genai.Client(api_key=config.GOOGLE_API_KEY)

def generate_tool_code(event):
    prompt = f"""
    You are an expert Python developer creating tools for an MCP (Model Context Protocol) server.
    
    Task: Create a FastMCP tool function based on the following recorded HTTP request.
    
    Request Details:
    - Method: {event['method']}
    - URL: {event['url']}
    - Headers: {event.get('request_headers', {})}
    - Body: {event.get('post_data', 'None')}
    
    Requirements:
    1. Use the `@mcp.tool()` decorator.
    2. Define the function as `async def`.
    3. Name the function descriptively based on the URL and action (e.g. `add_card`, `get_board`).
    4. Use `httpx` for the HTTP request (assume `httpx` is already imported).
    5. Include a detailed docstring explaining what the tool does.
    6. Handle errors gracefully.
    7. Return the response text or JSON.
    8. DO NOT include any imports (e.g. `import httpx`) in your output. They are already in the file header.
    9. ONLY output the Python code, no markdown formatting.
    
    Output Code:
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt
        )
        return response.text.replace("```python", "").replace("```", "").strip()
    except Exception as e:
        log(f"Error generating code: {e}")
        return ""

def process_events():
    if not os.path.exists(config.EVENTS_LOG):
        print(f"No events file found at {config.EVENTS_LOG}")
        return

    with open(config.EVENTS_LOG, 'r') as f:
        events = json.load(f)
    
    print(f"Processing {len(events)} events...")
    
    generated_code = []
    
    # Imports header
    header = """
import httpx
from mcp.server.fastmcp import FastMCP, Context

# Assumes 'mcp' object is available in the exec context or we import it here if running standalone
# But for dynamic loading, we might rely on the server's context. 
# Best practice: make tools standalone-ish or accept a session.
"""
    generated_code.append(header)

    for i, event in enumerate(events):
        log(f"Generating tool for Event {i+1}: {event['method']} {event['url']}")
        code = generate_tool_code(event)
        if code:
            generated_code.append(f"\n# Tool for {event['url']}\n{code}\n")
    
    # Save to file
    with open(config.GENERATED_TOOLS_FILE, "w") as f:
        f.write("\n".join(generated_code))
    

def log(msg):
    try:
        with open("gen_log.txt", "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass

if __name__ == "__main__":
    # Clear log
    with open("gen_log.txt", "w") as f:
        f.write("Starting generation...\n")
        
    process_events()
