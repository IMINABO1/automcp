from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import re
import config
from ask_watson import ask_watson


def generate_tool_code(event):
    """Generate MCP tool code for a single event."""

    # Use AI context if available for better understanding
    ai_context = event.get("ai_context", {})
    purpose = ai_context.get("purpose", "Unknown purpose")
    category = ai_context.get("category", "other")

    prompt = f"""
    You are an expert Python developer creating tools for an MCP (Model Context Protocol) server.

    Task: Create a FastMCP tool function based on the following recorded HTTP request.

    Request Details:
    - Method: {event['method']}
    - URL: {event['url']}
    - Headers: {json.dumps(event.get('request_headers', {}), indent=2)}
    - Body: {event.get('post_data', 'None')}

    AI Analysis of this endpoint:
    - Purpose: {purpose}
    - Category: {category}

    Requirements:
    1. Use the `@mcp.tool()` decorator.
    2. Define the function as `async def`.
    3. Name the function descriptively based on the PURPOSE (e.g. `get_board_cards`, `create_card`, `get_notifications`).
    4. Use `httpx` for the HTTP request (assume `httpx` and `mcp` are already imported).
    5. Include a detailed docstring explaining what the tool does based on the PURPOSE.
    6. Extract URL parameters as function arguments where appropriate.
    7. For AUTHENTICATION: Use `cookies=get_request_cookies(url)` to get session cookies. This function is already imported.
    8. For POST/PUT/DELETE requests: Include `"dsc": get_csrf_token()` in the request data/body for CSRF protection. The `get_csrf_token()` function is already imported.
    9. Handle errors gracefully.
    10. Return the response JSON or text.
    11. DO NOT include any imports. They are already in the file header.
    12. ONLY output the Python code, no markdown formatting.
    13. DO NOT hardcode any authentication tokens or cookies - always use get_request_cookies().

    Example for GET request:
    ```
    @mcp.tool()
    async def get_board_data(board_id: str):
        url = f"https://trello.com/1/boards/{{board_id}}"
        cookies = get_request_cookies(url)
        async with httpx.AsyncClient() as client:
            response = await client.get(url, cookies=cookies)
            return response.json()
    ```

    Example for POST request:
    ```
    @mcp.tool()
    async def create_card(list_id: str, name: str):
        url = "https://trello.com/1/cards"
        cookies = get_request_cookies(url)
        data = {{"idList": list_id, "name": name, "dsc": get_csrf_token()}}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, cookies=cookies, data=data)
            return response.json()
    ```

    Output Code:
    """

    try:
        response = ask_watson(prompt)
        code = response.replace("```python", "").replace("```", "").strip()
        return code
    except Exception as e:
        log(f"Error generating code: {e}")
        return ""


def deduplicate_events(events):
    """Remove duplicate endpoints based on URL pattern."""
    seen_patterns = set()
    unique_events = []

    for event in events:
        url = event.get("url", "")
        # Normalize URL by removing IDs and query params for deduplication
        # Keep the base pattern
        pattern = re.sub(r'/[a-f0-9]{24}', '/{id}', url)  # Trello IDs
        pattern = re.sub(r'/[a-zA-Z0-9]{8}', '/{shortId}', pattern)  # Short IDs
        pattern = pattern.split('?')[0]  # Remove query params

        if pattern not in seen_patterns:
            seen_patterns.add(pattern)
            unique_events.append(event)
        else:
            log(f"Skipping duplicate pattern: {pattern}")

    return unique_events


def process_events():
    # Try enriched file first, fall back to regular
    enriched_path = config.EVENTS_LOG.replace(".json", "_enriched.json")
    events_file = enriched_path if os.path.exists(enriched_path) else config.EVENTS_LOG

    if not os.path.exists(events_file):
        print(f"No events file found at {events_file}")
        return

    with open(events_file, 'r') as f:
        events = json.load(f)

    print(f"Loaded {len(events)} events from {events_file}")

    # Filter to only useful events
    useful_events = [
        e for e in events
        if e.get("ai_context", {}).get("useful_for_tool", False)
    ]

    if not useful_events:
        print("No events marked as useful_for_tool. Using all non-analytics events...")
        useful_events = [
            e for e in events
            if not any(skip in e.get("url", "") for skip in ["analytics", "sentry", "batch", "heartbeat", "gasv3", "xp.atlassian"])
        ]

    print(f"Filtered to {len(useful_events)} useful events")

    # Deduplicate similar endpoints
    unique_events = deduplicate_events(useful_events)
    print(f"After deduplication: {len(unique_events)} unique endpoints")

    # Header with imports
    # Note: mcp is provided by server.py via exec() execution_context
    # DO NOT create a new FastMCP instance here - it would override the server's instance
    header = '''"""
Auto-generated MCP tools from browser recording.
Generated by AutoMCP.

Note: This file is loaded via exec() by server.py which provides:
- mcp: FastMCP instance for tool registration
- httpx: HTTP client library
- get_request_cookies: Function to get cookies for a URL
- get_csrf_token: Function to get CSRF token
"""

import httpx
from session_utils import get_request_cookies, get_csrf_token

# mcp is provided by server.py via execution_context - do not instantiate here

'''

    generated_code = [header]

    # Generate tools in parallel
    print(f"\nGenerating {len(unique_events)} tools in parallel...")

    def generate_with_index(args):
        idx, event = args
        return idx, generate_tool_code(event), event

    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(generate_with_index, (i, e)): i for i, e in enumerate(unique_events)}
        done_count = 0
        for future in as_completed(futures):
            done_count += 1
            print(f"\r  Generated {done_count}/{len(unique_events)} tools...", end="", flush=True)
            try:
                idx, code, event = future.result()
                results[idx] = (code, event)
            except Exception as e:
                log(f"Error: {e}")

    print()  # newline

    # Add tools in order
    for i in range(len(unique_events)):
        if i in results:
            code, event = results[i]
            if code:
                purpose = event.get("ai_context", {}).get("purpose", event["url"])
                generated_code.append(f"\n# Tool: {purpose}\n{code}\n")
                log(f"Generated tool for: {purpose}")

    # Save to file
    with open(config.GENERATED_TOOLS_FILE, "w") as f:
        f.write("\n".join(generated_code))

    print(f"\nSaved generated tools to {config.GENERATED_TOOLS_FILE}")


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
