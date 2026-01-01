# RAG 시스템 프로토타입 요구사항

## 프로젝트 개요
- **목적**: RAG 시스템의 핵심 기능을 검증하기 위한 최소 기능 프로토타입 구현
- **범위**: 문서 관리 → 텍스트 처리 → 임베딩 → 검색까지 (답변 생성 제외)
- **기간**: 2-3주 개발

## 아키텍처 원칙

### API 설계 원칙 (Facade 패턴)
- **Facade 패턴**: `rag_service.py`가 복잡한 내부 시스템의 단순화된 인터페이스 제공
- **단일 진입점**: 모든 공개 API는 `rag_service.py` 파일에 집중
- **명확한 경계**: 공개 함수(언더스코어 없음) vs 내부 함수(`_`로 시작)
- **내부 구현 은닉**: `core/_*.py` 파일들은 외부에서 직접 접근 불가
- **명시적 공개**: `__all__`로 공개 API 목록 선언

### Facade 패턴 구조
- **목적**: 복잡한 하위 시스템들을 단순한 인터페이스로 통합
- **장점**:
  - 클라이언트와 구현 간의 느슨한 결합
  - 내부 구조 변경이 외부에 영향 없음
  - 사용이 간단하고 직관적
- **구현 방식**:
  - `rag_service.py`: Facade 클래스/함수 집합
  - `core/_*.py`: 하위 시스템 컴포넌트들
  - 클라이언트는 Facade만 알면 됨

### 파일 구조
```
RAG/
├── rag_service.py         # 🔥 유일한 공개 인터페이스
├── core/
│   ├── _*.py             # 모든 내부 구현 (private)
│   └── ...
└── ...
```

## 핵심 기능 요구사항

### 1. 문서 관리 (Document Management)
- **지원 형식**: PDF, TXT 파일만 지원 (MVP)
- **업로드**: 단일/다중 파일 업로드 기능
- **메타데이터**: 파일명, 업로드 시간, 파일 크기 자동 저장
- **저장**: 로컬 파일 시스템 기반 저장
- **문서 목록**: 업로드된 문서 리스트 조회

### 2. 텍스트 추출 및 정제 (Text Extraction)
- **PDF 처리**: PyPDF2 또는 pdfplumber를 사용한 텍스트 추출
- **텍스트 정제**:
  - 불필요한 공백 제거
  - 특수문자 정리
  - 줄바꿈 정규화
- **언어**: 한국어, 영어 지원

### 3. 문서 청킹 (Document Chunking)
- **청킹 전략**:
  - 토큰 기반 청킹 (tiktoken 라이브러리 사용)
  - 최대 토큰: 512 토큰 (OpenAI 임베딩 모델 고려)
  - 오버랩: 50 토큰
  - 문장 경계 유지 옵션
- **청크 메타데이터**:
  - 원본 문서 ID
  - 청크 순서 번호
  - 청크 내용
  - 토큰 수

### 4. 임베딩 생성 (Embedding Generation)
- **임베딩 모델**:
  - OpenAI text-embedding-ada-002 (다국어 지원)
  - 또는 text-embedding-3-small (비용 효율적, 다국어 지원)
- **벡터 저장 및 관리**:
  - FAISS 인덱스 사용 (효율적인 검색)
  - 청크 ID와 벡터 매핑 테이블 유지
  - 문서 삭제 시 관련 벡터 자동 제거
- **배치 처리**:
  - 최대 20개 텍스트/배치 (API 제한)
  - 재시도 로직 포함

### 5. 검색 기능 (Search)
- **쿼리 처리**:
  - 사용자 질의를 임베딩으로 변환
  - 코사인 유사도 기반 검색
- **검색 결과**:
  - Top-K 유사 청크 반환 (기본값: 5개)
  - 유사도 점수 포함
  - 원본 문서 정보 표시
- **결과 표시**:
  - 검색된 청크 내용
  - 소스 문서명
  - 관련도 점수

## 기술 스택

### Core Library (Python 모듈)
- **언어**: Python 3.9+
- **구조**: 일반 Python 함수/클래스 기반
- **문서 처리**:
  - PyPDF2 / pdfplumber (PDF)
  - python-docx (추후 확장용)
- **임베딩**:
  - Option 1: OpenAI API
  - Option 2: sentence-transformers (로컬)
- **벡터 저장**: NumPy + Pickle 또는 FAISS
- **데이터 저장**: SQLite (메타데이터)

### UI (Optional)
- **옵션 1**: Streamlit (웹 UI가 필요한 경우)
- **옵션 2**: Jupyter Notebook (대화형 테스트)
- **옵션 3**: CLI (커맨드라인 인터페이스)

## 데이터 구조

### 1. Document
```python
{
    "id": "uuid",
    "filename": "example.pdf",
    "upload_time": "2024-01-01T10:00:00",
    "file_size": 1024000,
    "status": "processed",
    "chunk_count": 50
}
```

### 2. Chunk
```python
{
    "id": "uuid",
    "document_id": "doc_uuid",
    "chunk_index": 0,
    "content": "청크 텍스트 내용...",
    "token_count": 450,
    "metadata": {
        "char_start": 0,
        "char_end": 2000,
        "embedding_id": "faiss_idx_123"  # FAISS 인덱스 내 위치
    }
}
```

### 3. Search Result
```python
{
    "query": "사용자 질의",
    "results": [
        {
            "chunk_id": "uuid",
            "document_name": "example.pdf",
            "content": "매칭된 청크 내용...",
            "similarity_score": 0.95,
            "chunk_index": 5
        }
    ]
}
```

### 4. ProcessStatus
```python
{
    "doc_id": "uuid",
    "status": "processing",  # pending, processing, completed, error
    "current_step": "embedding",  # upload, extraction, chunking, embedding, indexing
    "progress": 65,  # 0-100
    "error_message": null,
    "started_at": "2024-01-01T10:00:00",
    "updated_at": "2024-01-01T10:05:00"
}
```

## 공개 서비스 API (rag_service.py)

모든 외부 공개 함수는 `rag_service.py` 파일에 집중되며, 내부 구현은 core 모듈에 위치합니다.

### 서비스 인터페이스 구조
```python
# rag_service.py
"""RAG 시스템 공개 서비스 API"""

__all__ = [
    # 문서 관리
    'upload_document',
    'list_documents',
    'get_document',
    'delete_document',

    # 문서 처리
    'process_document',
    'get_processing_status',

    # 검색
    'search',

    # 평가
    'evaluate_search_quality'
]

# === 문서 관리 API ===
def upload_document(file_path: str) -> str:
    """
    문서 업로드 (공개 API)

    Args:
        file_path: 업로드할 파일 경로 (PDF/TXT)
    Returns:
        document_id: 생성된 문서 ID
    Raises:
        ValueError: 지원하지 않는 파일 형식
        FileNotFoundError: 파일이 존재하지 않음
    """

def list_documents() -> List[Document]:
    """
    업로드된 문서 목록 조회 (공개 API)

    Returns:
        List[Document]: 문서 목록
    """

def get_document(doc_id: str) -> Document:
    """
    문서 상세 정보 조회 (공개 API)

    Args:
        doc_id: 문서 ID
    Returns:
        Document: 문서 정보
    Raises:
        DocumentNotFoundError: 문서를 찾을 수 없음
    """

def delete_document(doc_id: str) -> bool:
    """
    문서 및 관련 데이터 삭제 (공개 API)

    Args:
        doc_id: 삭제할 문서 ID
    Returns:
        bool: 삭제 성공 여부
    Note:
        관련 청크와 벡터도 함께 삭제됨
    """

# === 문서 처리 API ===
def process_document(doc_id: str, callback: Callable = None) -> ProcessStatus:
    """
    문서 전체 처리 파이프라인 실행 (공개 API)

    Args:
        doc_id: 처리할 문서 ID
        callback: 진행 상태 콜백 (step: str, progress: int) -> None
    Returns:
        ProcessStatus: 최종 처리 상태
    Pipeline:
        1. 텍스트 추출
        2. 텍스트 정제
        3. 청킹 (토큰 기반)
        4. 임베딩 생성
        5. 인덱싱
    """

def get_processing_status(doc_id: str) -> ProcessStatus:
    """
    문서 처리 상태 조회 (공개 API)

    Args:
        doc_id: 상태 조회할 문서 ID
    Returns:
        ProcessStatus: 현재 처리 상태
    """

# === 검색 API ===
def search(query: str, top_k: int = 5) -> List[SearchResult]:
    """
    의미 기반 검색 수행 (공개 API)

    Args:
        query: 검색 질의
        top_k: 반환할 결과 개수
    Returns:
        List[SearchResult]: 검색 결과 (유사도 점수 포함)
    """

# === 평가 API ===
def evaluate_search_quality(eval_dataset: List[Dict]) -> Dict:
    """
    검색 품질 평가 (공개 API)

    Args:
        eval_dataset: 평가 데이터셋 (질의-정답 쌍)
    Returns:
        Dict: 평가 지표 (precision@5, MRR 등)
    """
```

### 내부 모듈 구조
```python
# core/ 디렉토리 - 내부 구현
core/
  ├── _document_manager.py   # 내부: 문서 관리 로직
  ├── _text_processor.py     # 내부: 텍스트 처리
  ├── _chunker.py           # 내부: 청킹 로직
  ├── _embeddings.py        # 내부: 임베딩 생성
  └── _search_engine.py     # 내부: 검색 엔진

# 내부 함수 예시 (core/_text_processor.py)
def _extract_text_from_pdf(file_path: str) -> str:
    """내부용: PDF 텍스트 추출"""

def _clean_text(text: str) -> str:
    """내부용: 텍스트 정제"""

def _tokenize_text(text: str) -> List[int]:
    """내부용: 토큰화"""
```

### 사용 예시
```python
# ✅ 올바른 사용법 - 공개 API만 사용
import rag_service

doc_id = rag_service.upload_document("document.pdf")
results = rag_service.search("검색 질의")

# ❌ 잘못된 사용법 - 내부 모듈 직접 접근
from core._document_manager import DocumentManager  # 금지!
from core import _text_processor  # 금지!
```

## 프로토타입 제한사항

1. **규모**: 최대 100개 문서, 10MB/파일
2. **동시성**: 단일 사용자 환경 가정
3. **보안**: 인증/권한 없음 (로컬 테스트용)
4. **성능**: 실시간 처리 불필요 (배치 처리 가능)
5. **UI**: 기본적인 기능만 제공

## 평가 데이터셋 구조

### 평가용 질의-정답 쌍
```json
{
  "eval_id": "eval_001",
  "query": "PDF 텍스트 추출 방법",
  "relevant_chunks": ["chunk_123", "chunk_456"],  // 정답 청크 ID
  "category": "technical",
  "difficulty": "easy"
}
```

### 평가 지표 계산
```python
def calculate_precision_at_k(results: List[str], relevant: List[str], k: int = 5) -> float:
    """Precision@K 계산"""

def calculate_mrr(results: List[str], relevant: List[str]) -> float:
    """Mean Reciprocal Rank 계산"""

def evaluate_search_quality(eval_dataset: List[Dict]) -> Dict:
    """전체 검색 품질 평가"""
```

## 테스트 시나리오

### 시나리오 1: 문서 업로드 및 처리
1. PDF 파일 3개 업로드
2. 각 문서 처리 (텍스트 추출 → 청킹 → 임베딩)
3. 처리 상태 확인
4. 문서 목록에서 확인

### 시나리오 2: 검색 테스트
1. 간단한 키워드 검색
2. 질문 형태 검색
3. Top-5 결과 확인
4. 유사도 점수 검증

### 시나리오 3: 성능 테스트
1. 50개 문서 일괄 처리
2. 검색 응답 시간 측정 (목표: 2초 이내)
3. 메모리 사용량 모니터링

## 개발 우선순위

### Phase 1 (1주차)
1. 프로젝트 구조 설정
2. 문서 업로드 기능
3. PDF 텍스트 추출
4. 텍스트 정제 및 청킹

### Phase 2 (2주차)
1. 임베딩 생성 (로컬 모델 우선)
2. 벡터 저장 및 인덱싱
3. 유사도 검색 구현
4. 통합 테스트

### Phase 3 (3주차) - Optional
1. UI 구현 (Streamlit/CLI)
2. 성능 최적화
3. 문서화
4. 예제 코드 작성

## 성공 기준

1. **기능적 완성도**
   - PDF/TXT 파일 정상 처리
   - 청킹 및 임베딩 생성 성공
   - 검색 결과 평가 지표:
     * Precision@5: 70% 이상
     * MRR (Mean Reciprocal Rank): 0.6 이상
     * 평가 데이터셋: 50개 질의-정답 쌍 준비

2. **성능**
   - 10MB 문서 처리: 30초 이내
   - 검색 응답: 2초 이내
   - 메모리 사용: 2GB 이하

3. **사용성**
   - 직관적인 인터페이스
   - 명확한 에러 메시지
   - 처리 상태 추적 가능 (ProcessStatus 객체 및 콜백)

## 향후 확장 계획

### 단기 (프로토타입 이후)
- Word, Markdown 파일 지원
- 하이브리드 검색 (벡터 + 키워드)
- 재순위화 (Re-ranking)
- 검색 필터링 기능

### 중기
- LLM 기반 답변 생성
- 멀티 언어 지원
- 사용자 인증
- 벡터 DB 도입 (Pinecone, Weaviate 등)

### 장기
- 실시간 처리 파이프라인
- 대용량 문서 지원
- 엔터프라이즈 통합
- 고급 분석 기능