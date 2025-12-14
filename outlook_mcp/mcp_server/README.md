# Outlook MCP Server

FastAPI-based MCP (Model Context Protocol) server for Microsoft Graph Mail API operations.

## Overview

This MCP server provides a standardized interface to interact with Microsoft Outlook emails through the Graph API. It routes MCP protocol requests to existing Graph Mail functions.

## Features

### Available MCP Tools

1. **query_emails** - Advanced email filtering with multiple criteria
2. **get_email** - Retrieve specific email by ID
3. **get_email_attachments** - List attachments for an email
4. **download_attachment** - Download specific attachment
5. **search_emails_by_date** - Search emails within date range
6. **send_email** - Send new email with attachments
7. **reply_to_email** - Reply to existing email
8. **forward_email** - Forward email to recipients
9. **delete_email** - Delete email by ID
10. **mark_as_read** - Mark email read/unread status

## Installation

```bash
# Install dependencies from mcp_server directory
cd /home/kimghw/Connector_auth/outlook_mcp/mcp_server
pip install -r requirements.txt
```

## Running the Server

```bash
# From mcp_server directory
cd /home/kimghw/Connector_auth/outlook_mcp/mcp_server
python run.py

# Or from project root
python outlook_mcp/mcp_server/run.py
```

Server will start at `http://localhost:3000`

## MCP Protocol Endpoints

- **POST /** - Main endpoint handling all MCP requests
  - `initialize` - Initialize server connection
  - `tools/list` - List available tools
  - `tools/call` - Execute specific tool

## Example MCP Request

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query_emails",
    "arguments": {
      "user_email": "user@example.com",
      "filter": {
        "from_address": "sender@example.com",
        "has_attachments": true,
        "received_after": "2024-01-01"
      },
      "top": 10
    }
  }
}
```

## Architecture

The MCP server acts as a routing layer:
- Receives MCP protocol requests
- Validates and parses parameters
- Routes to appropriate `GraphMailQuery` or `GraphMailClient` methods
- Returns formatted MCP responses

## Authentication

Authentication is handled automatically through the parent `auth` module:
- Tokens are retrieved from `auth.db`
- Token refresh is handled transparently
- User must be authenticated before using MCP tools

## Error Handling

Standard MCP error codes:
- `-32601`: Method not found
- `-32602`: Invalid parameters
- `-32603`: Internal error

## Development

To modify or extend:
1. Add new tool definitions to `MCP_TOOLS` list
2. Create corresponding handler function
3. Add routing in `handle_tool_call()`
4. Update this documentation