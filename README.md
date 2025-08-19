# Python MCP Markdownify Server

This is a pure Python implementation of the Markdownify MCP server using FastAPI and the official Model Context Protocol (MCP) Python SDK. It provides the same functionality as the original Node.js version but with a Python-only stack.

## Features

- Convert multiple file types to Markdown:
  - PDF
  - Images
  - Audio (with transcription)
  - DOCX
  - XLSX
  - PPTX
- Convert web content to Markdown:
  - YouTube video transcripts
  - Bing search results
  - General web pages
- Retrieve existing Markdown files

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install `uv` and Python dependencies:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   ```

## Usage

Start the server:
```bash
python server.py
```

The server will start on `http://localhost:3000` by default.

To integrate this server with a desktop app, add the following to your app's server configuration:

```json
{
  "mcpServers": {
    "markdownify-python": {
      "command": "python",
      "args": [
        "{ABSOLUTE PATH TO FILE HERE}/python-mcp-server/server.py"
      ],
      "env": {
        "UV_PATH": "/path/to/uv"
      }
    }
  }
}
```