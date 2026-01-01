"""
RAG System - Retrieval Augmented Generation Prototype
RAG 시스템 프로토타입 패키지

Usage:
    import rag_service

    # Upload and process document
    doc_id = rag_service.upload_document("document.pdf")
    status = rag_service.process_document(doc_id)

    # Search
    results = rag_service.search("your query")

    # Evaluate
    metrics = rag_service.evaluate_search_quality(eval_data)
"""

__version__ = "0.1.0"
__author__ = "RAG Development Team"

# Import all public APIs from rag_service
from .rag_service import *

# Version info
VERSION_INFO = {
    'major': 0,
    'minor': 1,
    'patch': 0,
    'stage': 'prototype'
}