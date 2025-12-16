#!/usr/bin/env python3
"""
Extract all functions decorated with @mcp_service from the codebase.

This script is now a thin wrapper around mcp_service_scanner.export_services_to_json
to avoid duplicated AST parsing logic.
"""

from __future__ import annotations

import os
from typing import Optional

from mcp_service_scanner import export_services_to_json


def main(server_name: Optional[str] = None):
    if server_name:
        base_dir = f"/home/kimghw/Connector_auth/mcp_{server_name}"
    else:
        base_dir = "/home/kimghw/Connector_auth/mcp_outlook"
        server_name = "outlook"

    print(f"Scanning for @mcp_service decorators in {base_dir} ...")
    output_dir = os.path.dirname(os.path.abspath(__file__))

    paths = export_services_to_json(base_dir, server_name, output_dir)

    print("\n=== Summary ===")
    print(f"Simple list saved to: {paths['simple']}")
    print(f"Detailed info saved to: {paths['detailed']}")
    if paths.get("legacy"):
        print(f"Legacy file saved to: {paths['legacy']}")


if __name__ == "__main__":
    import sys

    cli_server = sys.argv[1] if len(sys.argv) > 1 else None
    if cli_server:
        print(f"Using server name from command line: {cli_server}")
    main(cli_server)
