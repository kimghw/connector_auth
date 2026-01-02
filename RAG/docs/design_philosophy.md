# 설계 철학: SRP와 실용주의의 균형

## 문제: 너무 많은 클래스

### SRP를 극단적으로 적용한 예시 (❌ 과도함)
```python
# 하나의 텍스트 처리를 위해 5개 클래스...
class TextLoader:
    def load(self, path): pass

class TextCleaner:
    def clean(self, text): pass

class TextNormalizer:
    def normalize(self, text): pass

class TextValidator:
    def validate(self, text): pass

class TextSaver:
    def save(self, text): pass

# 사용할 때도 복잡
loader = TextLoader()
cleaner = TextCleaner()
normalizer = TextNormalizer()
validator = TextValidator()
saver = TextSaver()

text = loader.load(path)
text = cleaner.clean(text)
text = normalizer.normalize(text)
if validator.validate(text):
    saver.save(text)
```

### 실용적인 SRP 적용 (✅ 적절함)
```python
class TextProcessor:
    """텍스트 처리 관련 책임만 담당"""

    def extract_text(self, file_path: str) -> str:
        """추출"""
        pass

    def clean_text(self, text: str) -> str:
        """정제"""
        pass

    def normalize_text(self, text: str) -> str:
        """정규화"""
        pass

# 사용이 간단
processor = TextProcessor()
text = processor.extract_text(path)
text = processor.clean_text(text)
text = processor.normalize_text(text)
```

## 균형점 찾기: 응집도(Cohesion) 기준

### 1. **관련된 기능은 묶기**
```python
# ❌ 너무 세분화
class PDFReader: pass
class PDFParser: pass
class PDFTextExtractor: pass

# ✅ 적절한 묶음
class PDFProcessor:
    def read_pdf(self): pass
    def parse_pdf(self): pass
    def extract_text(self): pass
```

### 2. **도메인 단위로 구성**
```python
# 도메인별 책임 분리
class DocumentDomain:
    """문서 도메인 - 문서 관련 모든 작업"""
    pass

class SearchDomain:
    """검색 도메인 - 검색 관련 모든 작업"""
    pass

class EmbeddingDomain:
    """임베딩 도메인 - 벡터화 관련 작업"""
    pass
```

### 3. **레이어별 분리**
```
Presentation Layer (1-2 클래스)
    └── RAGService (Facade)

Application Layer (3-4 클래스)
    ├── DocumentService
    ├── SearchService
    └── ProcessingService

Domain Layer (5-6 클래스)
    ├── Document
    ├── Chunk
    ├── SearchResult
    └── ProcessStatus

Infrastructure Layer (4-5 클래스)
    ├── VectorStore
    ├── Database
    ├── FileStorage
    └── ExternalAPIClient
```

## RAG 시스템의 적절한 클래스 수

### 현재 설계 (적절함 ✅)
```
총 클래스: ~15-20개

- Data Models: 4개
- Enums: 2개
- Interfaces: 6개
- Implementations: 6개
- Facade: 1개
- Utilities: 2-3개
```

### 너무 많은 경우 (❌)
```
총 클래스: 50개+

- 각 메서드마다 클래스
- 모든 validation에 별도 클래스
- 모든 transformation에 별도 클래스
```

## 실용적 가이드라인

### 클래스를 분리할 때
1. **변경 이유가 다른가?**
   - Yes → 분리
   - No → 합치기

2. **재사용 가능성이 있는가?**
   - Yes → 분리
   - No → 합치기 고려

3. **테스트가 복잡한가?**
   - Yes → 분리
   - No → 현재 유지

4. **의존성이 다른가?**
   - Yes → 분리
   - No → 합치기 가능

### 클래스를 합칠 때
1. **항상 함께 사용되는가?**
   - Yes → 합치기 고려

2. **같은 데이터를 다루는가?**
   - Yes → 합치기 가능

3. **같은 추상화 수준인가?**
   - Yes → 합치기 가능

## 프로토타입 → 프로덕션 진화

### Phase 1: 프로토타입 (현재)
```python
# 단순하게 시작
class RAGSystem:
    def upload_document(self): pass
    def process_document(self): pass
    def search(self): pass
```

### Phase 2: 리팩토링
```python
# 책임 분리
class DocumentManager: pass
class TextProcessor: pass
class SearchEngine: pass
```

### Phase 3: 프로덕션
```python
# 인터페이스 도입
class IDocumentManager(Protocol): pass
class DocumentManagerImpl: pass
# + 의존성 주입
```

## 결론

### 좋은 설계의 특징
1. **이해하기 쉬움** - UML이 명확
2. **변경하기 쉬움** - 영향 범위 제한
3. **테스트하기 쉬움** - 모킹 가능
4. **과하지 않음** - 실용적

### 나쁜 설계의 징후
1. **God Class** - 하나가 너무 많은 일
2. **Ravioli Code** - 너무 잘게 쪼개짐
3. **Circular Dependencies** - 순환 참조
4. **Feature Envy** - 다른 클래스 데이터 과다 참조

## 추천 도구

### 복잡도 측정
```bash
# Radon - 복잡도 분석
radon cc . -a  # Cyclomatic Complexity
radon mi . -s  # Maintainability Index

# 기준
# CC: A(1-5) 좋음, B(6-10) 보통, C(11-20) 복잡
# MI: A(20+) 좋음, B(10-19) 보통, C(0-9) 나쁨
```

### 의존성 분석
```python
# pydeps - 의존성 그래프
pip install pydeps
pydeps RAG --max-bacon=2
```

## 실용적 RAG 설계

현재 interface_spec.py는 적절한 균형을 유지하고 있습니다:
- ✅ 도메인별 분리 (Document, Search, Embedding)
- ✅ 명확한 책임 (각 인터페이스)
- ✅ Facade로 복잡도 숨김
- ✅ 15-20개 정도의 적절한 클래스 수