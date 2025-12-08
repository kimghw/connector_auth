# Attachment MCP - 간단한 첨부파일 텍스트 변환

모든 종류의 첨부파일을 텍스트로 변환하는 간단한 Python 모듈

## 설치

```bash
# 기본 (텍스트, HTML, JSON, CSV)
# 추가 설치 없이 바로 사용 가능

# PDF 지원
pip install pypdf  # 또는 pymupdf, pdfplumber

# Word 지원
pip install python-docx

# HWP 지원
pip install olefile

# OCR 지원 (이미지)
pip install pytesseract pillow
```

## 사용법 - 정말 간단합니다!

### 1. 기본 사용법 (한 줄!)

```python
from attachment_mcp import convert_to_text

# 어떤 파일이든 그냥 넣으세요
text = convert_to_text("document.pdf")
text = convert_to_text("report.docx")
text = convert_to_text("data.csv")
text = convert_to_text("page.html")
```

### 2. URL에서 직접 변환

```python
text = convert_to_text("https://example.com/document.pdf")
```

### 3. 여러 파일 한번에

```python
from attachment_mcp import batch_convert

texts = batch_convert(["file1.pdf", "file2.txt", "file3.html"])
# 결과: {"file1.pdf": "텍스트...", "file2.txt": "텍스트...", ...}
```

### 4. 더 간단하게!

```python
from attachment_mcp import quick_convert

# 하나 파일
text = quick_convert("document.pdf")

# 여러 파일
texts = quick_convert("doc1.pdf", "doc2.txt", "doc3.html")
```

### 5. 지원 확인

```python
from attachment_mcp import is_supported

if is_supported("myfile.xyz"):
    text = convert_to_text("myfile.xyz")
else:
    print("지원하지 않는 파일 형식")
```

## 지원 파일 형식

### 기본 지원 (추가 설치 없음)
- **텍스트**: `.txt`, `.md`, `.log`, `.rst`
- **웹**: `.html`, `.htm`, `.xml`
- **데이터**: `.json`, `.csv`, `.tsv`

### 추가 라이브러리 필요
- **PDF**: `.pdf` (pypdf 설치)
- **Word**: `.docx`, `.doc` (python-docx 설치)
- **한글**: `.hwp`, `.hwpx` (olefile 설치)
- **이미지**: `.jpg`, `.png`, `.gif`, `.bmp` (pytesseract 설치)

## 특징

✅ **간단한 인터페이스** - 복잡한 설정 없이 바로 사용
✅ **자동 인코딩 감지** - UTF-8, CP949, EUC-KR 등 자동 처리
✅ **URL 지원** - 파일 다운로드 없이 직접 변환
✅ **일괄 처리** - 여러 파일 동시 변환
✅ **에러 처리** - 실패해도 안전하게 처리

## 예제

### 실제 사용 예제

```python
from attachment_mcp import convert_to_text

# 이메일 첨부파일 처리
attachments = ["contract.pdf", "report.docx", "data.csv"]
for file in attachments:
    try:
        content = convert_to_text(file)
        print(f"{file}: {len(content)} 글자 추출")
    except Exception as e:
        print(f"{file}: 변환 실패 - {e}")
```

### 메일과 연동

```python
# Outlook 메일 첨부파일 처리
from outlook_mcp import get_attachments
from attachment_mcp import convert_to_text

# 메일에서 첨부파일 다운로드
files = get_attachments(mail_id)

# 모든 첨부파일을 텍스트로
for file_path in files:
    text = convert_to_text(file_path)
    # 텍스트 처리...
```

## API 레퍼런스

### 메인 함수

- `convert_to_text(file_path_or_url, **kwargs)` - 파일을 텍스트로 변환
- `batch_convert(file_list, **kwargs)` - 여러 파일 일괄 변환
- `is_supported(file_path)` - 지원 여부 확인
- `quick_convert(*files)` - 가장 간단한 변환

### 특화 함수

- `extract_pdf_text(pdf_path)` - PDF 전용
- `extract_word_text(word_path)` - Word 전용
- `extract_from_url(url)` - URL 전용

## 라이선스

MIT