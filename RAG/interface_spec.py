"""
RAG System Interface Specification
RAG 시스템 인터페이스 명세서

이 파일은 RAG 시스템의 전체 인터페이스를 정의합니다.
- 데이터 모델 (Data Models)
- 예외 클래스 (Exceptions)
- 프로토콜 정의 (Protocols)
- API 함수 시그니처 (Function Signatures)

실제 사용자 호출은 rag_service.py를 통해 이루어집니다.
"""

from typing import List, Dict, Optional, Callable, Any, Protocol
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np


# =======================
# Enumerations
# =======================

class DocumentStatus(Enum):
    """문서 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    DELETED = "deleted"


class ProcessingStep(Enum):
    """문서 처리 단계"""
    UPLOAD = "upload"
    EXTRACTION = "extraction"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"


# =======================
# Data Models
# =======================

class Document:
    """문서 정보 모델"""

    def __init__(self,
                 doc_id: str,
                 filename: str,
                 file_path: str,
                 file_size: int,
                 upload_time: datetime,
                 status: DocumentStatus,
                 chunk_count: int = 0,
                 error_message: Optional[str] = None):
        self.id = doc_id
        self.filename = filename
        self.file_path = file_path
        self.file_size = file_size
        self.upload_time = upload_time
        self.status = status
        self.chunk_count = chunk_count
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "upload_time": self.upload_time.isoformat(),
            "status": self.status.value,
            "chunk_count": self.chunk_count,
            "error_message": self.error_message
        }


class Chunk:
    """문서 청크 모델"""

    def __init__(self,
                 chunk_id: str,
                 document_id: str,
                 chunk_index: int,
                 content: str,
                 token_count: int,
                 char_start: int,
                 char_end: int,
                 embedding_id: Optional[str] = None):
        self.id = chunk_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.content = content
        self.token_count = token_count
        self.char_start = char_start
        self.char_end = char_end
        self.embedding_id = embedding_id

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "token_count": self.token_count,
            "metadata": {
                "char_start": self.char_start,
                "char_end": self.char_end,
                "embedding_id": self.embedding_id
            }
        }


class SearchResult:
    """검색 결과 모델"""

    def __init__(self,
                 chunk_id: str,
                 document_id: str,
                 document_name: str,
                 content: str,
                 similarity_score: float,
                 chunk_index: int):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.document_name = document_name
        self.content = content
        self.similarity_score = similarity_score
        self.chunk_index = chunk_index

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "content": self.content,
            "similarity_score": self.similarity_score,
            "chunk_index": self.chunk_index
        }


class ProcessStatus:
    """문서 처리 상태 모델"""

    def __init__(self,
                 doc_id: str,
                 status: DocumentStatus,
                 current_step: ProcessingStep,
                 progress: int,
                 error_message: Optional[str] = None,
                 started_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.doc_id = doc_id
        self.status = status
        self.current_step = current_step
        self.progress = progress  # 0-100
        self.error_message = error_message
        self.started_at = started_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "doc_id": self.doc_id,
            "status": self.status.value,
            "current_step": self.current_step.value,
            "progress": self.progress,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# =======================
# Custom Exceptions
# =======================

class RAGException(Exception):
    """RAG 시스템 기본 예외"""
    pass


class DocumentNotFoundError(RAGException):
    """문서를 찾을 수 없음"""
    pass


class ProcessingError(RAGException):
    """문서 처리 중 오류"""
    pass


class InvalidFileFormatError(RAGException):
    """지원하지 않는 파일 형식"""
    pass


class VectorIndexError(RAGException):
    """벡터 인덱스 관련 오류"""
    pass


class EmbeddingError(RAGException):
    """임베딩 생성 오류"""
    pass


# =======================
# Protocol Definitions (인터페이스 규약)
# =======================

class IDocumentManager(Protocol):
    """문서 관리자 인터페이스"""

    def upload(self, file_path: str) -> str:
        """문서 업로드"""
        ...

    def list_all(self, status: Optional[DocumentStatus] = None) -> List[Document]:
        """문서 목록 조회"""
        ...

    def get_by_id(self, doc_id: str) -> Document:
        """문서 조회"""
        ...

    def delete(self, doc_id: str) -> bool:
        """문서 삭제"""
        ...


class ITextProcessor(Protocol):
    """텍스트 처리기 인터페이스"""

    def extract_text(self, file_path: str) -> str:
        """텍스트 추출"""
        ...

    def clean_text(self, text: str) -> str:
        """텍스트 정제"""
        ...

    def normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        ...


class IChunker(Protocol):
    """청킹 처리기 인터페이스"""

    def create_chunks(self, text: str, max_tokens: int = 512,
                     overlap_tokens: int = 50) -> List[Dict[str, Any]]:
        """텍스트를 청크로 분할"""
        ...

    def count_tokens(self, text: str) -> int:
        """토큰 수 계산"""
        ...


class IEmbeddingGenerator(Protocol):
    """임베딩 생성기 인터페이스"""

    def generate_embedding(self, text: str) -> np.ndarray:
        """단일 텍스트 임베딩 생성"""
        ...

    def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """배치 임베딩 생성"""
        ...

    @property
    def dimension(self) -> int:
        """임베딩 차원"""
        ...


class ISearchEngine(Protocol):
    """검색 엔진 인터페이스"""

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """검색 수행"""
        ...

    def search_with_filter(self, query: str, filters: SearchFilter,
                          top_k: int = 5) -> List[SearchResult]:
        """필터링 검색 - SearchFilter 타입 사용"""
        ...


class IVectorStore(Protocol):
    """벡터 저장소 인터페이스"""

    def add_vector(self, chunk_id: str, vector: np.ndarray) -> bool:
        """벡터 추가"""
        ...

    def search_vectors(self, query_vector: np.ndarray,
                      top_k: int = 5) -> List[tuple[str, float]]:
        """벡터 검색"""
        ...

    def delete_vector(self, chunk_id: str) -> bool:
        """벡터 삭제"""
        ...

    def get_vector(self, chunk_id: str) -> Optional[np.ndarray]:
        """벡터 조회"""
        ...

    def rebuild_index(self) -> bool:
        """인덱스 재구축"""
        ...


# =======================
# Abstract Base Classes (구현 템플릿)
# =======================

class BaseProcessor(ABC):
    """기본 처리기 추상 클래스"""

    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """처리 메서드 - 하위 클래스에서 구현 필요"""
        pass

    def validate_input(self, input_data: Any) -> bool:
        """입력 검증 (선택적 구현)"""
        return True

    def post_process(self, result: Any) -> Any:
        """후처리 (선택적 구현)"""
        return result


# Import types from types.py to avoid duplication
from .types import (
    DocumentId, ChunkId, EmbeddingVector, ProgressCallback,
    EvaluationDataset, SearchFilter, ProcessingConfig, SystemStats,
    ValidationResult
)


# =======================
# API Function Signatures (Module-level)
# =======================

def upload_document(file_path: str) -> str:
    """문서 업로드"""
    raise NotImplementedError("This is an interface specification")


def list_documents(status: Optional[DocumentStatus] = None,
                   limit: int = 100,
                   offset: int = 0) -> List[Document]:
    """문서 목록 조회"""
    raise NotImplementedError("This is an interface specification")


def get_document(doc_id: str) -> Document:
    """문서 상세 정보 조회"""
    raise NotImplementedError("This is an interface specification")


def delete_document(doc_id: str) -> bool:
    """문서 삭제"""
    raise NotImplementedError("This is an interface specification")


def process_document(doc_id: str,
                     callback: Optional[ProgressCallback] = None,
                     max_tokens: int = 512,
                     overlap_tokens: int = 50) -> ProcessStatus:
    """문서 처리 파이프라인 실행"""
    raise NotImplementedError("This is an interface specification")


def get_processing_status(doc_id: str) -> ProcessStatus:
    """처리 상태 조회"""
    raise NotImplementedError("This is an interface specification")


def search(query: str,
           top_k: int = 5,
           similarity_threshold: float = 0.0) -> List[SearchResult]:
    """의미 기반 검색"""
    raise NotImplementedError("This is an interface specification")


def search_with_filter(query: str,
                       filters: SearchFilter,
                       top_k: int = 5) -> List[SearchResult]:
    """필터링 검색 - SearchFilter 타입 사용"""
    raise NotImplementedError("This is an interface specification")


def get_supported_formats() -> List[str]:
    """지원 파일 형식 조회"""
    raise NotImplementedError("This is an interface specification")


def validate_file(file_path: str) -> ValidationResult:
    """파일 유효성 검증"""
    raise NotImplementedError("This is an interface specification")


# Import Config from types.py
from .types import Config


# =======================
# Export list
# =======================

__all__ = [
    # Enumerations
    'DocumentStatus',
    'ProcessingStep',

    # Data Models
    'Document',
    'Chunk',
    'SearchResult',
    'ProcessStatus',

    # Custom Exceptions
    'RAGException',
    'DocumentNotFoundError',
    'ProcessingError',
    'InvalidFileFormatError',
    'VectorIndexError',
    'EmbeddingError',

    # Protocol Definitions
    'IDocumentManager',
    'ITextProcessor',
    'IChunker',
    'IEmbeddingGenerator',
    'ISearchEngine',
    'IVectorStore',

    # Abstract Base Classes
    'BaseProcessor',

    # API Functions (Core API only)
    'upload_document',
    'list_documents',
    'get_document',
    'delete_document',
    'process_document',
    'get_processing_status',
    'search',
    'search_with_filter',
    'get_supported_formats',
    'validate_file',

    # Configuration
    'Config',
]