#!/usr/bin/env python3

import os
import tempfile
import shutil
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool
from pydantic import BaseModel
import httpx
import markitdown

# Initialize FastAPI app and FastMCP server
app = FastAPI()
mcp = FastMCP("python-mcp-markdownify-server")

# Models for tool arguments
class YouTubeToMarkdownArgs(BaseModel):
    url: str

class PDFToMarkdownArgs(BaseModel):
    filepath: str

class BingSearchResultToMarkdownArgs(BaseModel):
    url: str

class WebpageToMarkdownArgs(BaseModel):
    url: str

class ImageToMarkdownArgs(BaseModel):
    filepath: str

class AudioToMarkdownArgs(BaseModel):
    filepath: str

class DocxToMarkdownArgs(BaseModel):
    filepath: str

class XlsxToMarkdownArgs(BaseModel):
    filepath: str

class PptxToMarkdownArgs(BaseModel):
    filepath: str

class GetMarkdownFileArgs(BaseModel):
    filepath: str

# Utility functions
def _is_private_ip(hostname: str) -> bool:
    """Check if a hostname resolves to a private IP address."""
    import ipaddress
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private
    except ValueError:
        # If it's not a direct IP, we'd need to resolve it
        # For simplicity, we'll skip complex DNS resolution here
        # and assume non-private for non-IP hostnames
        return False

def _normalize_path(filepath: str) -> str:
    """Normalize a file path."""
    return os.path.normpath(os.path.expanduser(filepath))

def _save_to_temp_file(content: bytes, suggested_extension: Optional[str] = None) -> str:
    """Save content to a temporary file."""
    extension = suggested_extension or "md"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}")
    temp_file.write(content)
    temp_file.close()
    return temp_file.name

async def _fetch_url_content(url: str) -> bytes:
    """Fetch content from a URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content

# Core conversion logic
async def _convert_to_markdown(
    filepath: Optional[str] = None,
    url: Optional[str] = None,
    project_root: Optional[str] = None,
    uv_path: Optional[str] = None,
) -> Dict[str, str]:
    """Convert a file or URL to Markdown using markitdown."""
    try:
        input_path: str = ""
        is_temporary: bool = False

        if url:
            # Validate URL
            if not url.startswith(("http://", "https://")):
                raise ValueError("Only http:// and https:// URLs are allowed.")
            
            # Simple check for private IP (in a real implementation, you'd want a more robust check)
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            if _is_private_ip(parsed_url.hostname or ""):
                raise ValueError(f"Fetching {url} is potentially dangerous, aborting.")
            
            # Fetch content
            content = await _fetch_url_content(url)
            
            # Determine extension
            extension = None
            if url.endswith(".pdf"):
                extension = "pdf"
            
            # Save to temporary file
            input_path = _save_to_temp_file(content, extension)
            is_temporary = True
        elif filepath:
            input_path = filepath
        else:
            raise ValueError("Either filepath or url must be provided")

        # Convert using markitdown
        result = markitdown.MarkItDown().convert(input_path)
        markdown_text = result.text
        
        # Save result to temporary file
        output_path = _save_to_temp_file(markdown_text.encode(), "md")
        
        # Clean up temporary input file if needed
        if is_temporary and os.path.exists(input_path):
            os.unlink(input_path)
            
        return {"path": output_path, "text": markdown_text}
    except Exception as e:
        raise Exception(f"Error processing to Markdown: {str(e)}")

async def _get_markdown_file(filepath: str) -> Dict[str, str]:
    """Get an existing Markdown file."""
    # Normalize path
    norm_path = _normalize_path(filepath)
    
    # Check file extension
    allowed_extensions = [".md", ".markdown"]
    if not any(norm_path.endswith(ext) for ext in allowed_extensions):
        raise ValueError("Required file is not a Markdown file.")
    
    # Check if file exists
    if not os.path.exists(norm_path):
        raise FileNotFoundError("File does not exist")
    
    # Check if file is within allowed directory (if configured)
    md_share_dir = os.environ.get("MD_SHARE_DIR")
    if md_share_dir:
        allowed_share_dir = _normalize_path(md_share_dir)
        if not os.path.commonpath([norm_path, allowed_share_dir]) == allowed_share_dir:
            raise PermissionError(f"Only files in {allowed_share_dir} are allowed.")
    
    # Read file content
    with open(norm_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return {"path": norm_path, "text": content}

# Define MCP tools
@mcp.tool(
    name="youtube-to-markdown",
    description="Convert a YouTube video to markdown, including transcript if available",
    arguments=YouTubeToMarkdownArgs
)
async def youtube_to_markdown(args: YouTubeToMarkdownArgs) -> Dict[str, str]:
    return await _convert_to_markdown(url=args.url)

@mcp.tool(
    name="pdf-to-markdown",
    description="Convert a PDF file to markdown",
    arguments=PDFToMarkdownArgs
)
async def pdf_to_markdown(args: PDFToMarkdownArgs) -> Dict[str, str]:
    return await _convert_to_markdown(filepath=args.filepath)

@mcp.tool(
    name="bing-search-to-markdown",
    description="Convert a Bing search results page to markdown",
    arguments=BingSearchResultToMarkdownArgs
)
async def bing_search_to_markdown(args: BingSearchResultToMarkdownArgs) -> Dict[str, str]:
    return await _convert_to_markdown(url=args.url)

@mcp.tool(
    name="webpage-to-markdown",
    description="Convert a webpage to markdown",
    arguments=WebpageToMarkdownArgs
)
async def webpage_to_markdown(args: WebpageToMarkdownArgs) -> Dict[str, str]:
    return await _convert_to_markdown(url=args.url)

@mcp.tool(
    name="image-to-markdown",
    description="Convert an image to markdown, including metadata and description",
    arguments=ImageToMarkdownArgs
)
async def image_to_markdown(args: ImageToMarkdownArgs) -> Dict[str, str]:
    return await _convert_to_markdown(filepath=args.filepath)

@mcp.tool(
    name="audio-to-markdown",
    description="Convert an audio file to markdown, including transcription if possible",
    arguments=AudioToMarkdownArgs
)
async def audio_to_markdown(args: AudioToMarkdownArgs) -> Dict[str, str]:
    return await _convert_to_markdown(filepath=args.filepath)

@mcp.tool(
    name="docx-to-markdown",
    description="Convert a DOCX file to markdown",
    arguments=DocxToMarkdownArgs
)
async def docx_to_markdown(args: DocxToMarkdownArgs) -> Dict[str, str]:
    return await _convert_to_markdown(filepath=args.filepath)

@mcp.tool(
    name="xlsx-to-markdown",
    description="Convert an XLSX file to markdown",
    arguments=XlsxToMarkdownArgs
)
async def xlsx_to_markdown(args: XlsxToMarkdownArgs) -> Dict[str, str]:
    return await _convert_to_markdown(filepath=args.filepath)

@mcp.tool(
    name="pptx-to-markdown",
    description="Convert a PPTX file to markdown",
    arguments=PptxToMarkdownArgs
)
async def pptx_to_markdown(args: PptxToMarkdownArgs) -> Dict[str, str]:
    return await _convert_to_markdown(filepath=args.filepath)

@mcp.tool(
    name="get-markdown-file",
    description="Get a markdown file by absolute file path",
    arguments=GetMarkdownFileArgs
)
async def get_markdown_file(args: GetMarkdownFileArgs) -> Dict[str, str]:
    return await _get_markdown_file(args.filepath)

# Mount MCP to FastAPI
app.mount("/mcp", mcp.streamable_http_app())

# Health check endpoint
@app.get("/")
async def health_check():
    return {"status": "ok", "server": "python-mcp-markdownify-server"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)