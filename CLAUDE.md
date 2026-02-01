# AutoMCP

Automated MCP (Model Context Protocol) tool generator for web applications.

## Project Overview

AutoMCP is an autonomous "Tool Factory" that generates MCP servers from website interactions. It captures browser actions and network traffic to automatically create Python-based MCP tools.

## Tech Stack

- **Python 3.12+** - Main language
- **MCP (FastMCP)** - Model Context Protocol server framework
- **Playwright** - Browser automation
- **Google Generative AI** - Tool generation
- **httpx** - HTTP client
- **python-dotenv** - Environment configuration

## Project Structure

```
automcp/
├── server.py          # MCP server entry point
├── generator.py       # Tool generation logic
├── recorder.py        # Browser action recorder
├── generated_tools.py # Auto-generated MCP tools
├── config.py          # Configuration settings
├── extension/         # Chrome extension for capturing actions
│   ├── manifest.json
│   ├── background.js
│   ├── popup.html
│   └── popup.js
└── session.json       # Captured session data
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

3. Run the MCP server:
   ```bash
   python server.py
   ```

## Key Files

- `server.py` - Main MCP server using FastMCP
- `recorder.py` - Captures browser interactions with Playwright
- `generator.py` - Uses AI to generate MCP tool code
- `generated_tools.py` - Output file with generated tool functions

## Development Commands

```bash
# Run the server
python server.py

# Run the recorder
python recorder.py

# Generate tools
python generator.py

# Check model configuration
python check_model.py
```

## Environment Variables

- `GOOGLE_API_KEY` - Google Generative AI API key (required for tool generation)
