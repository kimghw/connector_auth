"""
Service Registry Module

서비스 레지스트리 관리:
- 서비스 메타데이터 로딩
- 레지스트리 파일 스캔
"""

import os
import json

from .config import BASE_DIR
from mcp_service_registry.mcp_service_scanner import get_services_map
from mcp_service_registry.meta_registry import MetaRegisterManager

# Module-level cache for service scans
SERVICE_SCAN_CACHE: dict[tuple[str, str], dict] = {}


def load_services_for_server(server_name: str | None, scan_dir: str | None, force_rescan: bool = False):
    """Load service metadata from registry JSON first, fallback to AST scanning."""
    if not server_name:
        return {}

    # Convert server_name to registry format (mcp_outlook -> outlook, mcp_file_handler -> file_handler)
    registry_name = server_name.replace("mcp_", "") if server_name and server_name.startswith("mcp_") else server_name

    # Try to load from registry JSON first (faster and more reliable)
    registry_path = os.path.join(BASE_DIR, "mcp_service_registry", f"registry_{registry_name}.json")

    # Check if registry file exists, if not log error and raise exception
    if not os.path.exists(registry_path):
        error_msg = f"Registry file not found: {registry_path}"
        print(f"ERROR: {error_msg}")
        raise FileNotFoundError(error_msg)

    if not force_rescan:
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                registry_data = json.load(f)
                services = {}
                for service_name, service_info in registry_data.get("services", {}).items():
                    services[service_name] = {
                        "signature": service_info.get("signature", ""),
                        "parameters": service_info.get("parameters", []),
                        "metadata": service_info.get("metadata", {}),
                    }
                print(f"Loaded {len(services)} services from registry_{registry_name}.json")
                return services
        except Exception as e:
            print(f"Warning: Could not load registry_{registry_name}.json: {e}")

    # Fallback to AST scanning if force_rescan is True
    if not scan_dir:
        return {}

    cache_key = (server_name or "", scan_dir)
    if not force_rescan and cache_key in SERVICE_SCAN_CACHE:
        print(f"Using cached service signatures for {cache_key[0] or 'default'}")
        return SERVICE_SCAN_CACHE[cache_key]

    services = get_services_map(scan_dir, server_name)
    SERVICE_SCAN_CACHE[cache_key] = services
    print(f"Extracted {len(services)} services from source code ({'rescan' if force_rescan else 'fresh'})")
    return services


def scan_all_registries():
    """Scan all profiles and update their registry files on startup."""
    try:
        from .config import _load_config_file

        config = _load_config_file()
        registry_manager = MetaRegisterManager()

        for profile_name, profile_config in config.items():
            # Skip merged profiles - they don't have their own service files
            if profile_config.get("is_merged"):
                print(f"  Skipping {profile_name}: merged profile (registry preserved)")
                continue

            source_dir = profile_config.get("source_dir")
            if not source_dir:
                print(f"  Skipping {profile_name}: no source_dir configured")
                continue

            # Resolve source_dir relative to BASE_DIR
            source_path = os.path.normpath(os.path.join(BASE_DIR, source_dir))
            if not os.path.exists(source_path):
                print(f"  Skipping {profile_name}: source_dir not found: {source_path}")
                continue

            # Extract server name (mcp_outlook -> outlook)
            server_name = profile_name.replace("mcp_", "") if profile_name.startswith("mcp_") else profile_name

            # Output path for registry
            registry_path = os.path.join(BASE_DIR, "mcp_service_registry", f"registry_{server_name}.json")

            print(f"  Scanning {profile_name} from {source_path}...")
            success = registry_manager.export_service_manifest(
                file_path=registry_path, base_dir=source_path, server_name=server_name
            )

            if success:
                print(f"    -> Updated {registry_path}")
            else:
                print(f"    -> Failed to update registry for {profile_name}")

    except Exception as e:
        print(f"Error scanning registries: {e}")
