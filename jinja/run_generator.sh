#!/bin/bash

# MCP Server Generator Usage Examples

echo "MCP Server Generator - Usage Examples"
echo "======================================"
echo ""

# Example 1: Basic usage with required arguments
echo "Example 1: Basic Outlook generation"
echo "python generate_server.py \\"
echo "  --tools ../mcp_editor/outlook/tool_definition_templates.py \\"
echo "  --server outlook \\"
echo "  --output ../mcp_outlook/mcp_server/server_generated.py"
echo ""

# Example 2: File Handler template
echo "Example 2: File Handler template"
echo "python generate_server.py \\"
echo "  --tools ../mcp_editor/file_handler/tool_definition_templates.py \\"
echo "  --server file_handler \\"
echo "  --output ../mcp_file_handler/mcp_server/server_generated.py"
echo ""

# Example 3: With custom template
echo "Example 3: Using custom template"
echo "python generate_server.py \\"
echo "  --tools ../mcp_editor/tool_definition_templates.py \\"
echo "  --template ./custom_template.jinja2 \\"
echo "  --output ../outlook_mcp/mcp_server/server_custom.py"
echo ""

# Example 4: Using JSON tool definitions
echo "Example 4: JSON input"
echo "python generate_server.py \\"
echo "  --tools ./tool_definitions.json \\"
echo "  --output ./generated_server.py"
echo ""

# Example 5: Scaffold template
echo "Example 5: Scaffold template"
echo "python generate_server.py \\"
echo "  --template ./mcp_server_scaffold_template.jinja2 \\"
echo "  --output ../mcp_new/mcp_server/server.py \\"
echo "  --server new_server"
echo ""

# Run actual generation with current setup (Outlook)
echo "Running actual generation..."
echo "----------------------------"
python generate_server.py \
  --tools ../mcp_editor/outlook/tool_definition_templates.py \
  --server outlook \
  --output ../mcp_outlook/mcp_server/server_generated.py
