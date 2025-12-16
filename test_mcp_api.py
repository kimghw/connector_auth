#!/usr/bin/env python3
"""
MCP API Test Script
Tests the MCP tool definitions and API endpoints
"""

import json
import sys
import os

# Add paths for imports
sys.path.insert(0, '.')

def test_file_handler_tools():
    """Test file_handler tool definitions"""
    print("\n=== FILE HANDLER TOOL DEFINITIONS TEST ===")
    print("-" * 50)

    try:
        from mcp_file_handler.mcp_server.tool_definitions import MCP_TOOLS, get_tool_names

        print(f"✅ Successfully loaded {len(MCP_TOOLS)} tools")
        print("\nAvailable tools:")
        for tool in MCP_TOOLS:
            print(f"  - {tool['name']:30} {tool['description'][:50]}...")

        # Test specific tool
        print("\nTesting 'convert_file_to_text' tool structure:")
        convert_tool = next((t for t in MCP_TOOLS if t['name'] == 'convert_file_to_text'), None)
        if convert_tool:
            print(f"  ✅ Found tool definition")
            print(f"  - Input schema type: {convert_tool['inputSchema']['type']}")
            print(f"  - Required params: {convert_tool['inputSchema'].get('required', [])}")
        else:
            print("  ❌ Tool not found")

    except Exception as e:
        print(f"❌ Error loading file_handler tools: {e}")
        return False

    return True


def test_outlook_tools():
    """Test outlook tool definitions"""
    print("\n=== OUTLOOK TOOL DEFINITIONS TEST ===")
    print("-" * 50)

    try:
        from mcp_outlook.mcp_server.tool_definitions import MCP_TOOLS, get_tool_names

        print(f"✅ Successfully loaded {len(MCP_TOOLS)} tools")
        print("\nAvailable tools:")
        for tool in MCP_TOOLS[:5]:  # Show first 5
            print(f"  - {tool['name']:30} {tool['description'][:50]}...")
        if len(MCP_TOOLS) > 5:
            print(f"  ... and {len(MCP_TOOLS) - 5} more")

    except Exception as e:
        print(f"❌ Error loading outlook tools: {e}")
        return False

    return True


def test_api_structure():
    """Test if API endpoints are structured correctly"""
    print("\n=== API STRUCTURE TEST ===")
    print("-" * 50)

    try:
        # Test file_handler server import
        from mcp_file_handler.mcp_server.server import app as fh_app
        print("✅ File handler FastAPI app loaded")

        # Check routes
        routes = [route.path for route in fh_app.routes]
        print(f"  Routes available: {len(routes)}")
        for route in routes[:5]:
            print(f"    - {route}")

    except Exception as e:
        print(f"❌ Error loading file_handler API: {e}")

    try:
        # Test outlook server import
        from mcp_outlook.mcp_server.server import app as ol_app
        print("\n✅ Outlook FastAPI app loaded")

        # Check routes
        routes = [route.path for route in ol_app.routes]
        print(f"  Routes available: {len(routes)}")
        for route in routes[:5]:
            print(f"    - {route}")

    except Exception as e:
        print(f"❌ Error loading outlook API: {e}")


def simulate_api_call():
    """Simulate an API call with tool definitions"""
    print("\n=== SIMULATED API CALL ===")
    print("-" * 50)

    try:
        from mcp_file_handler.mcp_server.tool_definitions import get_tool_by_name

        # Simulate getting a tool for API response
        tool = get_tool_by_name("convert_file_to_text")
        if tool:
            print("Simulated API response for /tools/convert_file_to_text:")
            print(json.dumps(tool, indent=2))
        else:
            print("❌ Tool not found")

    except Exception as e:
        print(f"❌ Error simulating API call: {e}")


def main():
    print("=" * 60)
    print("MCP API AND TOOL DEFINITIONS TEST")
    print("=" * 60)

    # Run tests
    fh_success = test_file_handler_tools()
    ol_success = test_outlook_tools()
    test_api_structure()
    simulate_api_call()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("-" * 60)
    print(f"File Handler Tools: {'✅ PASS' if fh_success else '❌ FAIL'}")
    print(f"Outlook Tools: {'✅ PASS' if ol_success else '❌ FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    main()