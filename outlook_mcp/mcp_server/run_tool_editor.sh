#!/bin/bash

# MCP Tool Editor Web Interface Launcher

echo "======================================"
echo "MCP Tool Definitions Editor"
echo "======================================"
echo ""

# Navigate to the script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install Flask flask-cors
else
    source venv/bin/activate
fi

# Create backups directory if it doesn't exist
mkdir -p backups

echo "Starting web server..."
echo "Access the editor at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

# Run the Flask app
python tool_editor_web.py