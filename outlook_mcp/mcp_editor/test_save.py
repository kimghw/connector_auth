#!/usr/bin/env python3
"""
Test script to update tool_definition_templates.py with signatures
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tool_editor_web import save_tool_definitions

# Get current tools from tool_definition_templates.py
import importlib.util
template_path = os.path.join(os.path.dirname(__file__), 'tool_definition_templates.py')
spec = importlib.util.spec_from_file_location("tool_definition_templates", template_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Clean up old mcp_service_signature fields if present
cleaned_tools = []
for tool in module.MCP_TOOLS:
    cleaned_tool = {k: v for k, v in tool.items() if k != 'mcp_service_signature'}
    cleaned_tools.append(cleaned_tool)

# Save with the cleaned data to trigger signature addition
result = save_tool_definitions(cleaned_tools)

if 'error' in result:
    print(f"Error: {result['error']}")
else:
    print(f"Success! Backup created: {result['backup']}")
    print(f"Files updated:")
    print(f"  - tool_definitions.py")
    print(f"  - tool_definition_templates.py (mcp_service is now an object with name and signature)")