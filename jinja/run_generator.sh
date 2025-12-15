#!/bin/bash

# MCP Server Generator Usage Examples

echo "MCP Server Generator - Usage Examples"
echo "======================================"
echo ""

# Example 1: Basic usage with required arguments
echo "Example 1: Basic generation"
echo "python generate_server.py \\"
echo "  --tools ../mcp_editor/tool_definition_templates.py \\"
echo "  --output ../outlook_mcp/mcp_server/server_generated.py"
echo ""

# Example 2: With custom template
echo "Example 2: Using custom template"
echo "python generate_server.py \\"
echo "  --tools ../mcp_editor/tool_definition_templates.py \\"
echo "  --template ./custom_template.jinja2 \\"
echo "  --output ../outlook_mcp/mcp_server/server_custom.py"
echo ""

# Example 3: With configuration file
echo "Example 3: Using configuration file"
echo "python generate_server.py \\"
echo "  --tools ../mcp_editor/tool_definition_templates.py \\"
echo "  --config ./config.json \\"
echo "  --output ../outlook_mcp/mcp_server/server_configured.py"
echo ""

# Example 4: Using JSON tool definitions
echo "Example 4: JSON input"
echo "python generate_server.py \\"
echo "  --tools ./tool_definitions.json \\"
echo "  --output ./generated_server.py"
echo ""

# Run actual generation with current setup
echo "Running actual generation..."
echo "----------------------------"
python generate_server.py \
  --tools ../mcp_editor/tool_definition_templates.py \
  --output ../outlook_mcp/mcp_server/server_generated.py