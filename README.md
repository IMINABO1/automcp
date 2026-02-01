# AutoMCP

An autonomous "Tool Factory" that automatically generates [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers from website interactions. AutoMCP captures browser actions and network traffic, then uses AI to create Python-based MCP tools that can replay those interactions programmatically.

## Overview

AutoMCP solves the problem of manually creating API integrations by automating the entire process:

1. **Record** - Launch a browser session and interact with any web application
2. **Capture** - Automatically intercept and log all network requests (API calls, form submissions, etc.)
3. **Analyze** - Use AI to understand the purpose of each captured request
4. **Generate** - Automatically create MCP-compatible tool functions for each useful endpoint
5. **Serve** - Run the generated tools as an MCP server that any MCP client can consume

This enables AI assistants to interact with web applications that don't have official APIs, or to quickly scaffold integrations with existing APIs.

## Features

- **Browser Recording**: Uses Playwright to launch a real browser session where you can interact with any website
- **AI-Powered Login**: Smart login agent that can navigate login flows, handle 2FA/OTP, and accept cookie banners
- **Network Capture**: Intercepts all XHR/Fetch requests and captures method, URL, headers, and body data
- **AI Analysis**: Each captured request is analyzed by IBM Watson (Granite model) to determine its purpose and usefulness
- **Code Generation**: Automatically generates async Python functions with proper authentication, CSRF handling, and error handling
- **MCP Server**: Generated tools are served via FastMCP, compatible with Claude Desktop and other MCP clients
- **Session Management**: Persists browser sessions and cookies for authenticated requests
- **Chrome Extension**: Optional extension for exporting cookies from your browser

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   recorder.py   │────▶│  generator.py   │────▶│   server.py     │
│                 │     │                 │     │                 │
│ - Browser auto  │     │ - AI analysis   │     │ - FastMCP       │
│ - Network capture│     │ - Code gen      │     │ - Tool hosting  │
│ - Session mgmt  │     │ - Deduplication │     │ - Hot reload    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
  session.json           generated_tools.py      MCP Client
  test_events.json                               (Claude, etc.)
```

## Installation

### Prerequisites

- Python 3.12 or higher
- A web browser (Chromium is used by Playwright)
- IBM Watson API credentials

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/IMINABO1/automcp.git
   cd automcp
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

5. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```env
   # IBM Watson Configuration
   IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
   IBM_API_KEY=your_ibm_api_key_here
   IBM_PROJECT_ID=your_project_id_here

   # Target website to record
   TARGET_URL=https://trello.com/b/yourboard
   ```

## Usage

### Step 1: Record Browser Session

Launch the recorder to capture network traffic from a website:

```bash
python recorder.py
```

This will:
1. Open a Chromium browser window
2. If no session exists, initiate the AI-powered login flow
3. Navigate to your `TARGET_URL`
4. Capture all network requests as you interact with the page
5. Save captured events to `test_events.json`
6. Analyze events with AI and save enriched data to `test_events_enriched.json`

**During recording:**
- The AI will prompt you for credentials if login is required
- Interact with the website normally - click buttons, submit forms, navigate pages
- All API calls are automatically captured in the background

### Step 2: Generate MCP Tools

Process the captured events and generate tool code:

```bash
python generator.py
```

This will:
1. Load events from `test_events_enriched.json`
2. Filter to only useful endpoints (excluding analytics, heartbeats, etc.)
3. Deduplicate similar API patterns
4. Generate Python code for each endpoint using AI
5. Save generated tools to `generated_tools.py`

### Step 3: Run the MCP Server

Start the MCP server to expose your generated tools:

```bash
python server.py
```

The server provides:
- All auto-generated tools from `generated_tools.py`
- A `reload_tools()` function to hot-reload tools without restarting

### Connecting to Claude Desktop

Add this to your Claude Desktop MCP configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "automcp": {
      "command": "python",
      "args": ["path/to/automcp/server.py"]
    }
  }
}
```

## Project Structure

```
automcp/
├── server.py           # MCP server entry point (FastMCP)
├── generator.py        # AI-powered tool code generation
├── recorder.py         # Browser automation and network capture
├── ask_watson.py       # IBM Watson AI integration
├── config.py           # Configuration and environment variables
├── session_utils.py    # Cookie and session management utilities
├── generated_tools.py  # Auto-generated MCP tools (output)
├── session.json        # Browser session state (cookies, storage)
├── test_events.json    # Raw captured network events
├── test_events_enriched.json  # Events with AI analysis
├── extension/          # Chrome extension for cookie export
│   ├── manifest.json
│   ├── background.js
│   ├── popup.html
│   └── popup.js
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── .gitignore
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `IBM_WATSONX_URL` | IBM Watson API endpoint | Yes |
| `IBM_API_KEY` | IBM Watson API key | Yes |
| `IBM_PROJECT_ID` | IBM Watson project ID | Yes |
| `TARGET_URL` | Website URL to record | Yes |

### AI Model

AutoMCP uses IBM Watson's Granite model (`ibm/granite-4-h-small`) for:
- Analyzing captured network requests
- Generating Python tool code

You can modify the model in `config.py`:
```python
IBM_MODEL_ID = "ibm/granite-4-h-small"
```

## Generated Tool Example

Here's an example of an auto-generated tool:

```python
@mcp.tool()
async def get_board_cards(board_id: str):
    """
    Retrieves all cards from a Trello board.

    Args:
        board_id: The ID of the board to fetch cards from

    Returns:
        JSON response containing card data
    """
    url = f"https://trello.com/1/boards/{board_id}/cards"
    cookies = get_request_cookies(url)
    async with httpx.AsyncClient() as client:
        response = await client.get(url, cookies=cookies)
        return response.json()
```

Generated tools automatically include:
- Proper async/await syntax
- Cookie-based authentication via `get_request_cookies()`
- CSRF token handling via `get_csrf_token()` for write operations
- Error handling
- Descriptive docstrings

## Chrome Extension

The included Chrome extension ("Cookie Snatcher") can export cookies from your browser for use with AutoMCP.

### Installation

1. Open Chrome and navigate to `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `extension/` folder
4. Click the extension icon on any website to export cookies

### Usage

The exported cookies can be saved to `cookies.json` for use when the recorder needs pre-authenticated sessions.

## Troubleshooting

### Login Issues

If the AI login agent struggles with a particular website:
1. Manually log in through the browser
2. Use the Chrome extension to export cookies
3. Save cookies to `session.json`

### Tool Generation Errors

Check `gen_log.txt` for detailed error messages during code generation.

### MCP Connection Issues

Ensure the server is running and check the MCP client configuration. The server outputs logs to stderr.

## Dependencies

- **mcp** (FastMCP) - Model Context Protocol server framework
- **playwright** - Browser automation
- **ibm-watsonx-ai** - IBM Watson AI integration
- **httpx** - Async HTTP client
- **python-dotenv** - Environment configuration
- **pyperclip** - Clipboard operations for OTP handling

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is open source. See the repository for license details.

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- [IBM watsonx.ai](https://www.ibm.com/watsonx) for AI capabilities
- [Playwright](https://playwright.dev/) for browser automation
