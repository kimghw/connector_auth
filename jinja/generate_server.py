#!/usr/bin/env python3
"""
Unified MCP server generator that selects the right Jinja template per server.

Exposes load_tool_definitions() and generate_server() so the web editor can call
it dynamically, while also providing a small CLI for manual use.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Ensure sibling generator modules can be imported when loaded via importlib
for path in (SCRIPT_DIR, PROJECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    from mcp_editor.tool_editor_web_server_mappings import get_server_name_from_path  # type: ignore
except Exception:
    def get_server_name_from_path(path: str) -> Optional[str]:
        """Minimal fallback when server mapping helpers are unavailable."""
        path = path or ""
        if "mcp_outlook" in path or "outlook" in path:
            return "outlook"
        if "file_handler" in path:
            return "file_handler"
        return None

from generate_outlook_server import (  # type: ignore
    generate_server as _generate_outlook_server,
    load_tool_definitions as _load_tool_definitions,
)

SERVER_TEMPLATE_MAP: Dict[str, str] = {
    "outlook": str(SCRIPT_DIR / "outlook_server_template.jinja2"),
    "file_handler": str(SCRIPT_DIR / "file_handler_server_template.jinja2"),
    "scaffold": str(SCRIPT_DIR / "mcp_server_scaffold_template.jinja2"),
}


def resolve_template_path(template_path: str | None = None, server_name: str | None = None) -> str:
    """Pick the best available template path based on explicit value, server, or defaults."""
    candidates: List[Path] = []

    if template_path:
        candidates.append(Path(template_path))

    if server_name and server_name in SERVER_TEMPLATE_MAP:
        candidates.append(Path(SERVER_TEMPLATE_MAP[server_name]))

    candidates.extend(Path(path) for path in SERVER_TEMPLATE_MAP.values())

    for candidate in candidates:
        if candidate and candidate.exists():
            return str(candidate)

    raise FileNotFoundError("No valid server template found in known locations")


def load_tool_definitions(tool_def_path: str) -> List[Dict[str, Any]]:
    """Load tool definitions using the shared outlook generator helper."""
    return _load_tool_definitions(tool_def_path)


def _render_scaffold_template(template_path: str, output_path: str, server_name: str | None):
    """Render the scaffold template which expects a server_name in context."""
    name = server_name or get_server_name_from_path(output_path) or "mcp_server"
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
    template = env.get_template(os.path.basename(template_path))
    rendered = template.render(server_name=name)
    Path(output_path).write_text(rendered)


def generate_server(
    template_path: str | None,
    output_path: str,
    tools: Optional[List[Dict[str, Any]]] = None,
    server_name: str | None = None
):
    """Generate server.py from tool definitions and the chosen template."""
    resolved_template = resolve_template_path(template_path, server_name)
    output_path = str(output_path)
    Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)

    if os.path.basename(resolved_template) == "mcp_server_scaffold_template.jinja2":
        _render_scaffold_template(resolved_template, output_path, server_name)
        return

    _generate_outlook_server(resolved_template, output_path, tools)


def _default_tools_path() -> Optional[str]:
    """Pick a sensible default tools path for CLI use."""
    candidates = [
        PROJECT_ROOT / "mcp_editor" / "tool_definition_templates.py",
        PROJECT_ROOT / "mcp_editor" / "outlook" / "tool_definition_templates.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def main():
    parser = argparse.ArgumentParser(description="Generate MCP server code from templates")
    default_tools = _default_tools_path()
    parser.add_argument(
        "--tools",
        "-t",
        default=default_tools,
        required=default_tools is None,
        help="Path to tool definition templates (.py or .json)",
    )
    parser.add_argument(
        "--template",
        "-p",
        help="Path to Jinja2 server template (defaults to server-specific template)",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output path for generated server.py",
    )
    parser.add_argument(
        "--server",
        "-s",
        help="Server name used to pick a template when --template is not provided",
    )

    args = parser.parse_args()

    tools: List[Dict[str, Any]] = []
    if args.template and os.path.basename(args.template) == "mcp_server_scaffold_template.jinja2":
        print("Rendering scaffold template (tool definitions not required)")
    else:
        if not args.tools:
            parser.error("--tools is required unless using the scaffold template")
        tools = load_tool_definitions(args.tools)
        print(f"Loaded {len(tools)} tool definitions from {args.tools}")

    generate_server(args.template, args.output, tools, server_name=args.server)
    print(f"Generated server to {args.output} using template {resolve_template_path(args.template, args.server)}")


if __name__ == "__main__":
    main()
