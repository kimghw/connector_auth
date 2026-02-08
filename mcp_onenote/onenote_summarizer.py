"""
OneNote Page Summarizer
HTML 파싱, 단락 추출, Claude Code SDK 기반 AI 요약/키워드 추출
"""

import os
import re
import hashlib
import logging
from html.parser import HTMLParser
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "summarize_config.yaml"
)


@dataclass
class Paragraph:
    """OneNote HTML에서 추출한 단락"""
    index: int
    text: str
    data_id: Optional[str] = None


class OneNoteHTMLParser(HTMLParser):
    """
    OneNote 페이지 HTML에서 단락을 추출하는 파서.
    <p>, <h1>~<h6>, <li> 태그를 단락으로 처리.
    """

    def __init__(self):
        super().__init__()
        self._paragraphs: List[Paragraph] = []
        self._current_text = ""
        self._current_data_id = None
        self._in_paragraph = False
        self._in_body = False
        self._para_tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li"}
        self._skip_tags = {"script", "style", "head"}
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "body":
            self._in_body = True
            return

        if tag in self._skip_tags:
            self._skip_depth += 1
            return

        if self._in_body and tag in self._para_tags and self._skip_depth == 0:
            self._in_paragraph = True
            self._current_text = ""
            self._current_data_id = attrs_dict.get("data-id")

    def handle_endtag(self, tag):
        if tag in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1
            return

        if tag == "body":
            self._in_body = False
            return

        if self._in_paragraph and tag in self._para_tags:
            text = self._current_text.strip()
            if text:
                self._paragraphs.append(Paragraph(
                    index=len(self._paragraphs),
                    text=text,
                    data_id=self._current_data_id,
                ))
            self._in_paragraph = False
            self._current_text = ""

    def handle_data(self, data):
        if self._in_paragraph and self._skip_depth == 0:
            self._current_text += data

    def get_paragraphs(self) -> List[Paragraph]:
        return self._paragraphs


def parse_html_to_paragraphs(html_content: str) -> List[Paragraph]:
    """OneNote HTML을 단락 리스트로 파싱"""
    parser = OneNoteHTMLParser()
    parser.feed(html_content)
    return parser.get_paragraphs()


def html_to_plain_text(html_content: str) -> str:
    """HTML을 평문 텍스트로 변환"""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&#\d+;', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def compute_content_hash(html_content: str) -> str:
    """콘텐츠 변경 감지용 SHA256 해시"""
    return hashlib.sha256(html_content.encode('utf-8')).hexdigest()


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """YAML 설정 파일 로드"""
    path = config_path or _DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        logger.warning(f"Config file not found: {path}, using defaults")
        return _default_config()

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _default_config() -> Dict[str, Any]:
    """기본 설정 (fallback)"""
    return {
        "summarization": {
            "page_summary": {
                "max_length": 500,
                "prompt": "다음 내용을 500자 이내로 요약해 주세요.\n\n페이지 제목: {page_title}\n\n{page_content}\n\n요약:",
            },
            "paragraph_summary": {
                "max_length": 200,
                "prompt": "다음 문단을 200자 이내로 요약해 주세요.\n\n{paragraph_text}\n\n요약:",
            },
            "keyword_extraction": {
                "count": 10,
                "prompt": "다음 내용에서 키워드를 {keyword_count}개 추출해 주세요. 쉼표로 구분.\n\n{page_title}\n\n{page_content}\n\n키워드:",
            },
        },
        "claude_sdk": {
            "model": "claude-sonnet-4-5-20250929",
            "max_turns": 1,
            "allowed_tools": [],
        },
    }


def is_sdk_available() -> bool:
    """Claude Code SDK 사용 가능 여부 확인 (현재 Claude Code 세션 기반)"""
    try:
        import claude_code_sdk  # noqa: F401
    except ImportError:
        return False
    return True


async def _call_claude_sdk(prompt: str, config: Dict[str, Any]) -> str:
    """Claude Code SDK로 프롬프트 전송 후 텍스트 응답 반환. SDK 미설치 시 빈 문자열."""
    try:
        from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock
    except ImportError:
        logger.debug("claude_code_sdk not installed, skipping")
        return ""

    sdk_config = config.get("claude_sdk", {})

    options = ClaudeCodeOptions(
        allowed_tools=sdk_config.get("allowed_tools", []),
        max_turns=sdk_config.get("max_turns", 1),
        model=sdk_config.get("model"),
    )

    try:
        response_texts = []
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_texts.append(block.text)
        return "\n".join(response_texts).strip()
    except Exception as e:
        logger.warning(f"Claude SDK 호출 실패: {e}")
        return ""


async def summarize_page(
    html_content: str,
    page_title: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    전체 요약 파이프라인: 페이지 요약 + 키워드 추출 (SDK 호출 2회)

    Returns:
        {
            "summary": str,
            "keywords": [str, ...],
            "content_hash": str,
        }
    """
    if config is None:
        config = load_config()

    summarization_config = config.get("summarization", {})

    # 1. HTML → 평문 변환 + 해시
    plain_text = html_to_plain_text(html_content)
    content_hash = compute_content_hash(html_content)

    # 2. 전체 페이지 요약 + 키워드 추출 (병렬 SDK 호출)
    import asyncio

    page_summary_config = summarization_config.get("page_summary", {})
    page_prompt = page_summary_config.get("prompt", "").format(
        page_title=page_title,
        page_content=plain_text[:8000],
    )

    keyword_config = summarization_config.get("keyword_extraction", {})
    keyword_count = keyword_config.get("count", 10)
    keyword_prompt = keyword_config.get("prompt", "").format(
        page_title=page_title,
        page_content=plain_text[:8000],
        keyword_count=keyword_count,
    )

    summary_raw, keywords_raw = await asyncio.gather(
        _call_claude_sdk(page_prompt, config),
        _call_claude_sdk(keyword_prompt, config),
    )

    max_length = page_summary_config.get("max_length", 500)
    summary = summary_raw[:max_length]
    keywords = [kw.strip() for kw in keywords_raw.split(",") if kw.strip()][:keyword_count]

    return {
        "summary": summary,
        "keywords": keywords,
        "content_hash": content_hash,
    }
