#!/usr/bin/env python
"""
MCP Server Launcher
Starts the FastAPI MCP server for Outlook Graph Mail
"""
import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Launch the MCP server"""
    print("=" * 60)
    print("Starting Outlook MCP Server")
    print("=" * 60)
    print("Server will be available at: http://localhost:3000")
    print("MCP Protocol Endpoints:")
    print("  - POST / (initialize, tools/list, tools/call)")
    print("=" * 60)

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()