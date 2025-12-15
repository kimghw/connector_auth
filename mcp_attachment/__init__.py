"""
Attachment MCP - 간단한 첨부파일 텍스트 변환 모듈

사용법:
    from attachment_mcp import convert_to_text

    # 단일 파일 변환
    text = convert_to_text("document.pdf")

    # URL에서 변환
    text = convert_to_text("https://example.com/file.pdf")

    # 여러 파일 한번에
    from attachment_mcp import batch_convert
    texts = batch_convert(["file1.pdf", "file2.txt", "file3.html"])
"""

# 간단한 API만 노출
from .simple_converter import (
    convert_to_text,
    extract_text,
    batch_convert,
    is_supported,
    extract_pdf_text,
    extract_word_text,
    extract_from_url,
    quick_convert
)

# 버전 정보
__version__ = "1.0.0"

# 공개 API
__all__ = [
    'convert_to_text',
    'extract_text',
    'batch_convert',
    'is_supported',
    'extract_pdf_text',
    'extract_word_text',
    'extract_from_url',
    'quick_convert'
]