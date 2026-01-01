# RAG 프로토타입 프로젝트 구조

## 디렉토리 구조
```
RAG/
├── rag_service.py             # 🔥 공개 서비스 API (외부 인터페이스)
│
├── core/                      # 내부 구현 (private)
│   ├── __init__.py
│   ├── _document_manager.py   # 내부: 문서 관리 로직
│   ├── _text_processor.py     # 내부: 텍스트 처리
│   ├── _chunker.py            # 내부: 청킹 로직
│   ├── _embeddings.py         # 내부: 임베딩 생성
│   └── _search_engine.py      # 내부: 검색 엔진
│
├── models/                    # 데이터 모델
│   ├── __init__.py
│   ├── document.py           # Document 클래스
│   ├── chunk.py              # Chunk 클래스
│   └── search_result.py      # SearchResult 클래스
│
├── storage/                   # 데이터 저장 관련
│   ├── __init__.py
│   ├── database.py           # SQLite 연결 및 쿼리
│   ├── vector_store.py       # 벡터 저장소 (NumPy/FAISS)
│   └── file_storage.py       # 파일 시스템 관리
│
├── utils/                     # 유틸리티 함수
│   ├── __init__.py
│   ├── config.py             # 설정 관리
│   ├── logger.py             # 로깅
│   └── text_utils.py         # 텍스트 처리 유틸
│
├── tests/                     # 테스트 코드
│   ├── __init__.py
│   ├── test_document.py
│   ├── test_chunker.py
│   ├── test_embeddings.py
│   └── test_search.py
│
├── examples/                  # 사용 예제
│   ├── simple_example.py     # 기본 사용법
│   ├── batch_processing.py   # 배치 처리 예제
│   └── search_demo.py        # 검색 데모
│
├── data/                      # 데이터 저장 디렉토리
│   ├── documents/            # 원본 문서 저장
│   ├── embeddings/           # 임베딩 벡터 저장
│   └── database/             # SQLite DB 파일
│
├── notebooks/                 # Jupyter 노트북 (테스트용)
│   ├── 01_data_processing.ipynb
│   ├── 02_embedding_test.ipynb
│   └── 03_search_evaluation.ipynb
│
├── requirements.txt           # 의존성 패키지
├── setup.py                   # 패키지 설정
├── config.yaml               # 설정 파일
├── README.md                 # 프로젝트 설명
└── .gitignore               # Git 제외 파일
```

## 주요 모듈 설명

### 1. rag_service.py (공개 API)
```python
"""RAG 시스템 공개 서비스 API"""

__all__ = [
    'upload_document',
    'list_documents',
    'get_document',
    'delete_document',
    'process_document',
    'get_processing_status',
    'search',
    'evaluate_search_quality'
]

# 공개 서비스 함수
def upload_document(file_path: str) -> str:
    """문서 업로드 (공개 API)"""
    from core._document_manager import DocumentManager
    dm = DocumentManager()
    return dm._upload(file_path)

def search(query: str, top_k: int = 5) -> List[SearchResult]:
    """검색 수행 (공개 API)"""
    from core._search_engine import SearchEngine
    se = SearchEngine()
    return se._search(query, top_k)

# ... 기타 공개 함수들
```

### 2. core/_document_manager.py (내부 구현)
```python
class DocumentManager:
    def __init__(self, storage_path: str):
        """문서 관리자 초기화"""

    def _upload(self, file_path: str) -> str:
        """내부: 문서 업로드 구현"""

    def _list_all(self) -> List[Document]:
        """내부: 문서 목록 조회"""

    def _get_by_id(self, doc_id: str) -> Document:
        """내부: 문서 조회"""

    def _delete(self, doc_id: str) -> bool:
        """내부: 문서 삭제"""

    def _validate_file(self, file_path: str):
        """내부: 파일 검증"""
```

### 3. core/_text_processor.py (내부 구현)
```python
class TextProcessor:
    def _extract_from_pdf(self, file_path: str) -> str:
        """내부: PDF 텍스트 추출"""

    def _extract_from_txt(self, file_path: str) -> str:
        """내부: 텍스트 파일 읽기"""

    def _clean(self, text: str) -> str:
        """내부: 텍스트 정제"""

    def _normalize(self, text: str) -> str:
        """내부: 텍스트 정규화"""
```

### 4. core/_chunker.py (내부 구현)
```python
import tiktoken

class TextChunker:
    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 50):
        """토큰 기반 청커 초기화"""
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    def _create_chunks(self, text: str) -> List[Dict]:
        """내부: 토큰 기반 청크 생성"""

    def _count_tokens(self, text: str) -> int:
        """내부: 토큰 수 계산"""
```

### 5. core/_embeddings.py (내부 구현)
```python
class EmbeddingGenerator:
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        """OpenAI 임베딩 생성기 초기화"""

    def _generate_single(self, text: str) -> np.ndarray:
        """내부: 단일 임베딩 생성"""

    def _generate_batch(self, texts: List[str]) -> np.ndarray:
        """내부: 배치 임베딩 생성 (최대 20개)"""
```

### 6. core/_search_engine.py (내부 구현)
```python
class SearchEngine:
    def __init__(self, vector_store):
        """검색 엔진 초기화"""

    def _search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """내부: 검색 수행"""

    def _calculate_similarity(self, query_embedding: np.ndarray,
                            corpus_embeddings: np.ndarray) -> np.ndarray:
        """내부: 코사인 유사도 계산"""
```

## 사용 예제

### 기본 사용법 (공개 API 사용)
```python
import rag_service

# 1. 문서 업로드
doc_id = rag_service.upload_document("example.pdf")
print(f"Document uploaded: {doc_id}")

# 2. 문서 처리 (콜백으로 진행상황 추적)
def progress_callback(step, progress):
    print(f"{step}: {progress}%")

status = rag_service.process_document(doc_id, callback=progress_callback)
print(f"Processing status: {status.status}")

# 3. 검색
results = rag_service.search("PDF 텍스트 추출 방법", top_k=5)
for result in results:
    print(f"Score: {result.similarity_score:.3f}")
    print(f"Content: {result.content[:200]}...")
    print(f"Source: {result.document_name}\n")

# 4. 문서 목록 조회
documents = rag_service.list_documents()
for doc in documents:
    print(f"{doc.id}: {doc.filename} ({doc.status})")

# 5. 검색 품질 평가
eval_data = [
    {"query": "PDF 처리", "relevant_chunks": ["chunk_123", "chunk_456"]}
]
metrics = rag_service.evaluate_search_quality(eval_data)
print(f"Precision@5: {metrics['precision_at_5']}")
print(f"MRR: {metrics['mrr']}")
```

## 설정 파일 (config.yaml)
```yaml
# 문서 처리 설정
document:
  max_file_size_mb: 10
  allowed_formats: ["pdf", "txt"]
  storage_path: "./data/documents"

# 청킹 설정 (토큰 기반)
chunking:
  max_tokens: 512
  overlap_tokens: 50
  preserve_sentence_boundary: true

# 임베딩 설정 (OpenAI)
embedding:
  model: "text-embedding-ada-002"
  batch_size: 20  # OpenAI API 제한 고려
  api_key_env: "OPENAI_API_KEY"  # 환경변수명

# 검색 설정
search:
  top_k: 5
  similarity_threshold: 0.7

# 데이터베이스 설정
database:
  path: "./data/database/rag.db"
```

## 의존성 패키지 (requirements.txt)
```
# 핵심 패키지
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=0.24.0

# 문서 처리
PyPDF2>=3.0.0
pdfplumber>=0.9.0
python-docx>=0.8.11

# OpenAI API
openai>=1.0.0
tiktoken>=0.5.0  # 토큰 카운팅

# 벡터 저장
faiss-cpu>=1.7.0

# 데이터베이스
sqlite3

# 유틸리티
pyyaml>=5.4
python-dotenv>=0.19.0
tqdm>=4.62.0


# 개발/테스트
pytest>=7.0.0
black>=22.0.0
flake8>=4.0.0
```