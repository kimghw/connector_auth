"""JavaScript language support for service registry."""
from .scanner import (
    ESPRIMA_AVAILABLE,
    JSDOC_TYPE_MAP,
    find_mcp_services_in_js_file,
    find_jsdoc_mcp_services_in_js_file,
)
from .types import (
    scan_js_project_types,
    export_js_types_property,
    extract_sequelize_models_from_file,
)

__all__ = [
    "ESPRIMA_AVAILABLE",
    "JSDOC_TYPE_MAP",
    "find_mcp_services_in_js_file",
    "find_jsdoc_mcp_services_in_js_file",
    "scan_js_project_types",
    "export_js_types_property",
    "extract_sequelize_models_from_file",
]
