"""
MCP OneNote Module
Microsoft Graph API를 사용한 OneNote 서비스 (mcp_outlook 구조 참조)
"""

from .onenote_service import OneNoteService
from .onenote_agent import OneNoteAgent
from .onenote_page import OneNotePageManager
from .onenote_db_query import OneNoteDBQuery
from .graph_onenote_client import GraphOneNoteClient
from .onenote_db_service import OneNoteDBService
from .onenote_types import (
    NotebookInfo,
    SectionInfo,
    PageInfo,
    PageContent,
    SummaryInfo,
    CreateSectionRequest,
    CreatePageRequest,
    UpdatePageRequest,
    SyncResult,
)
from .onenote_agent import (
    parse_html_to_paragraphs,
    html_to_plain_text,
    compute_content_hash,
    load_config,
    is_sdk_available,
)

__all__ = [
    # Service
    "OneNoteService",
    # Agent
    "OneNoteAgent",
    # Page Manager
    "OneNotePageManager",
    # DB Query
    "OneNoteDBQuery",
    # Client
    "GraphOneNoteClient",
    # DB Service
    "OneNoteDBService",
    # Agent utilities
    "parse_html_to_paragraphs",
    "html_to_plain_text",
    "compute_content_hash",
    "load_config",
    "is_sdk_available",
    # Types
    "NotebookInfo",
    "SectionInfo",
    "PageInfo",
    "PageContent",
    "SummaryInfo",
    "CreateSectionRequest",
    "CreatePageRequest",
    "UpdatePageRequest",
    "SyncResult",
]

__version__ = "1.0.0"
