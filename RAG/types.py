"""
RAG System Type Definitions
타입 힌트 및 타입 별칭 정의
"""

from typing import TypedDict, List, Dict, Optional, Union, Any, Callable
from datetime import datetime
import numpy as np


# =======================
# Type Aliases
# =======================

DocumentId = str
ChunkId = str
EmbeddingVector = np.ndarray
TokenList = List[int]
ProgressCallback = Callable[[str, int], None]


# =======================
# TypedDict Definitions
# =======================

class EvaluationDataset(TypedDict):
    """평가 데이터셋 구조"""
    eval_id: str
    query: str
    relevant_chunks: List[ChunkId]
    category: Optional[str]
    difficulty: Optional[str]


class SearchFilter(TypedDict, total=False):
    """검색 필터 옵션"""
    document_ids: Optional[List[DocumentId]]
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    categories: Optional[List[str]]
    min_score: Optional[float]


class ChunkMetadata(TypedDict):
    """청크 메타데이터"""
    char_start: int
    char_end: int
    embedding_id: Optional[str]
    token_count: int


class ProcessingConfig(TypedDict, total=False):
    """문서 처리 설정"""
    max_tokens: int
    overlap_tokens: int
    preserve_sentence_boundary: bool
    batch_size: int
    embedding_model: str


class ValidationResult(TypedDict):
    """파일 검증 결과"""
    valid: bool
    format: str
    size: int
    error: Optional[str]


class SystemStats(TypedDict):
    """시스템 통계"""
    total_documents: int
    total_chunks: int
    total_vectors: int
    index_size_mb: float
    processing_queue: int
    last_updated: datetime


class EvaluationMetrics(TypedDict):
    """검색 평가 지표"""
    precision_at_5: float
    precision_at_10: float
    mrr: float
    total_queries: int
    avg_response_time_ms: Optional[float]


# =======================
# Protocol Definitions
# =======================

from typing import Protocol


class DocumentStore(Protocol):
    """문서 저장소 프로토콜"""

    def save_document(self, doc_id: DocumentId, content: bytes) -> bool:
        ...

    def load_document(self, doc_id: DocumentId) -> bytes:
        ...

    def delete_document(self, doc_id: DocumentId) -> bool:
        ...

    def exists(self, doc_id: DocumentId) -> bool:
        ...


class VectorStore(Protocol):
    """벡터 저장소 프로토콜"""

    def add_vector(self, chunk_id: ChunkId, vector: EmbeddingVector) -> bool:
        ...

    def search_vectors(self, query_vector: EmbeddingVector, top_k: int) -> List[tuple[ChunkId, float]]:
        ...

    def delete_vector(self, chunk_id: ChunkId) -> bool:
        ...

    def get_vector(self, chunk_id: ChunkId) -> Optional[EmbeddingVector]:
        ...


class EmbeddingModel(Protocol):
    """임베딩 모델 프로토콜"""

    def embed_text(self, text: str) -> EmbeddingVector:
        ...

    def embed_batch(self, texts: List[str]) -> List[EmbeddingVector]:
        ...

    @property
    def dimension(self) -> int:
        ...


# =======================
# Constants
# =======================

class Config:
    """시스템 설정 상수"""

    # File limits
    MAX_FILE_SIZE_MB = 10
    SUPPORTED_FORMATS = [".pdf", ".txt"]

    # Chunking defaults
    DEFAULT_MAX_TOKENS = 512
    DEFAULT_OVERLAP_TOKENS = 50

    # Embedding settings
    EMBEDDING_MODEL = "text-embedding-ada-002"
    EMBEDDING_DIMENSION = 1536
    EMBEDDING_BATCH_SIZE = 20

    # Search settings
    DEFAULT_TOP_K = 5
    DEFAULT_SIMILARITY_THRESHOLD = 0.0

    # Processing
    MAX_CONCURRENT_PROCESSING = 3
    PROCESSING_TIMEOUT_SECONDS = 300

    # Storage paths
    DOCUMENT_STORAGE_PATH = "./data/documents"
    VECTOR_STORAGE_PATH = "./data/embeddings"
    DATABASE_PATH = "./data/database/rag.db"