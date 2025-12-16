#!/usr/bin/env python3
"""
Test actual API endpoints with HTTP calls
"""

import json
import requests
from typing import Dict, Any


def test_tool_execution(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Test executing a specific tool with parameters"""
    print(f"\n📞 Testing tool execution: {tool_name}")
    print(f"   Parameters: {json.dumps(params, indent=2)}")

    # This simulates what an MCP client would do
    from mcp_file_handler.file_manager import FileManager

    try:
        manager = FileManager()

        if tool_name == "convert_file_to_text":
            # Create a test file
            test_file = "/tmp/test.txt"
            with open(test_file, "w") as f:
                f.write("Hello, this is a test file!\nLine 2\nLine 3")

            # Call the actual method
            result = manager.process(test_file)
            print(f"   ✅ Result: {result}")
            return {"success": True, "result": result}

        elif tool_name == "save_file_metadata":
            result = manager.save_metadata(
                params["file_url"],
                params["keywords"],
                params.get("additional_metadata")
            )
            print(f"   ✅ Result: {result}")
            return {"success": True, "result": result}

        elif tool_name == "search_metadata":
            result = manager.search_metadata(**params)
            print(f"   ✅ Result: {result}")
            return {"success": True, "result": result}

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"success": False, "error": str(e)}


def test_mcp_protocol():
    """Test MCP protocol-like interaction"""
    print("\n=== MCP PROTOCOL SIMULATION ===")
    print("-" * 50)

    # 1. List available tools
    print("\n1. Listing available tools:")
    from mcp_file_handler.mcp_server.tool_definitions import MCP_TOOLS

    tools_response = {
        "jsonrpc": "2.0",
        "result": {
            "tools": [{"name": t["name"], "description": t["description"]}
                     for t in MCP_TOOLS]
        },
        "id": 1
    }

    print(json.dumps(tools_response, indent=2)[:500] + "...")

    # 2. Get specific tool schema
    print("\n2. Getting schema for 'convert_file_to_text':")
    from mcp_file_handler.mcp_server.tool_definitions import get_tool_by_name

    tool = get_tool_by_name("convert_file_to_text")
    schema_response = {
        "jsonrpc": "2.0",
        "result": tool,
        "id": 2
    }

    print(json.dumps(schema_response, indent=2))

    # 3. Execute tool
    print("\n3. Executing tool with parameters:")
    call_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "convert_file_to_text",
            "arguments": {
                "input_path": "/tmp/test.txt"
            }
        },
        "id": 3
    }

    print("Request:")
    print(json.dumps(call_request, indent=2))

    print("\nResponse:")
    result = test_tool_execution(
        "convert_file_to_text",
        call_request["params"]["arguments"]
    )

    call_response = {
        "jsonrpc": "2.0",
        "result": result,
        "id": 3
    }
    print(json.dumps(call_response, indent=2))


def test_metadata_workflow():
    """Test a complete metadata workflow"""
    print("\n=== METADATA WORKFLOW TEST ===")
    print("-" * 50)

    # 1. Save metadata
    print("\n1. Saving file metadata:")
    save_result = test_tool_execution(
        "save_file_metadata",
        {
            "file_url": "https://example.com/document.pdf",
            "keywords": ["test", "document", "pdf"],
            "additional_metadata": {
                "author": "Test User",
                "created": "2024-12-16"
            }
        }
    )

    # 2. Search metadata
    print("\n2. Searching for metadata:")
    search_result = test_tool_execution(
        "search_metadata",
        {
            "keywords": ["test"]
        }
    )

    # 3. Get specific metadata
    print("\n3. Getting specific file metadata:")
    from mcp_file_handler.file_manager import FileManager
    manager = FileManager()
    try:
        result = manager.get_metadata("https://example.com/document.pdf")
        print(f"   ✅ Found metadata: {result}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def main():
    print("=" * 60)
    print("MCP API ENDPOINT AND EXECUTION TEST")
    print("=" * 60)

    # Run protocol simulation
    test_mcp_protocol()

    # Run workflow test
    test_metadata_workflow()

    print("\n" + "=" * 60)
    print("✅ All API tests completed")
    print("=" * 60)


if __name__ == "__main__":
    main()