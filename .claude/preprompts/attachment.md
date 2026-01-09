# 메일 첨부파일 처리 API 가이드

## 1. 개요

메일 첨부파일을 조회하고 처리하는 외부 API 인터페이스 설명.
내부 구현은 고려하지 않고, **호출 가능한 함수와 옵션**만 정의함.

---

## 2. 조회 방식

### 2.1 조회 파라미터

| 파라미터 | 필수 | 설명 |
|---------|:----:|------|
| `user_email` | ✅ | 사용자 이메일 (user_id) |
| `message_ids` | ✅ | 메일 ID 목록 |
| `attachment_id` | ❌ | 특정 첨부파일 ID (선택적) |

### 2.2 조회 유형

| 조회 방식 | 함수 | 설명 |
|----------|------|------|
| **Batch** (message_id만) | `BatchAttachmentHandler.fetch_and_save()` | 여러 메일의 모든 첨부파일 일괄 처리 |
| **Batch** (메타데이터만) | `BatchAttachmentHandler.fetch_metadata_only()` | 첨부파일 다운로드 없이 메타정보만 조회 |
| **Single** (message_id + attachment_id) | `BatchAttachmentHandler.fetch_specific_attachments()` | 특정 첨부파일만 선택 다운로드 |
| **Single** (첨부파일 목록) | `SingleAttachmentHandler.list_attachments()` | 특정 메일의 첨부파일 목록 조회 |
| **Single** (첨부파일 상세) | `SingleAttachmentHandler.get_attachment()` | 특정 첨부파일 상세 정보 조회 |

---

## 3. 진입 함수 (Entry Points)

### 3.1 BatchAttachmentHandler

```python
from mcp_outlook.mail_attachment import BatchAttachmentHandler

handler = BatchAttachmentHandler(
    base_directory="downloads",           # 로컬 저장 기본 경로
    metadata_file="mail_metadata.json"    # 중복 관리용 메타데이터 파일
)
```

#### 3.1.1 fetch_and_save() - 배치 조회 + 저장

```python
result = await handler.fetch_and_save(
    # === 필수 ===
    user_email: str,                      # 사용자 이메일
    message_ids: List[str],               # 메일 ID 목록

    # === 조회 옵션 ===
    select_params: SelectParams = None,   # 추가 조회 필드

    # === 저장 옵션 ===
    save_file: bool = True,               # 저장 여부 (False면 메모리 반환만)
    storage_type: str = "local",          # "local" | "onedrive"
    onedrive_folder: str = "/Attachments",# OneDrive 저장 경로

    # === 변환 옵션 ===
    convert_to_txt: bool = False,         # TXT 변환 여부

    # === 본문 옵션 ===
    include_body: bool = True,            # 본문 포함 여부

    # === 중복 처리 ===
    skip_duplicates: bool = True,         # 이미 처리된 메일 건너뛰기
)
```

> **참고**: `save_file=False`면 저장하지 않고 변환된 내용을 메모리로 반환
> **참고**: `include_body=False`면 첨부파일만 처리 (본문 제외)

#### 3.1.2 fetch_metadata_only() - 메타데이터만 조회

```python
result = await handler.fetch_metadata_only(
    user_email: str,
    message_ids: List[str],
    select_params: SelectParams = None,
)
```

#### 3.1.3 fetch_specific_attachments() - 특정 첨부파일 다운로드

```python
result = await handler.fetch_specific_attachments(
    user_email: str,
    attachments_info: List[Dict[str, str]],  # [{"message_id": "...", "attachment_id": "..."}]
    save_directory: str = None,
)
```

---

### 3.2 SingleAttachmentHandler

```python
from mcp_outlook.mail_attachment import SingleAttachmentHandler

handler = SingleAttachmentHandler(access_token="...")
```

#### 3.2.1 list_attachments() - 첨부파일 목록 조회

```python
attachments = await handler.list_attachments(
    message_id: str,
    user_id: str = "me",    # 사용자 이메일 또는 "me"
)
```

#### 3.2.2 get_attachment() - 첨부파일 상세 조회

```python
attachment = await handler.get_attachment(
    message_id: str,
    attachment_id: str,
    user_id: str = "me",
)
```

#### 3.2.3 download_attachment() - 첨부파일 다운로드

```python
saved_path = await handler.download_attachment(
    message_id: str,
    attachment_id: str,
    save_path: str = None,  # None이면 downloads/{message_id[:8]}/
    user_id: str = "me",
)
```

---

## 4. 옵션 조합표

### 4.1 전체 옵션 조합

| save_file | convert_to_txt | storage_type | include_body | 결과 |
|:---------:|:--------------:|:------------:|:------------:|------|
| `False` | `False` | - | - | 원본 조회 → 메모리 반환 |
| `False` | `True` | - | - | TXT 변환 → 메모리 반환 |
| `True` | `False` | `"local"` | `True` | 원본 + 본문 → 로컬 저장 |
| `True` | `False` | `"local"` | `False` | 원본만 → 로컬 저장 |
| `True` | `True` | `"local"` | `True` | TXT 변환 + 본문 → 로컬 저장 |
| `True` | `False` | `"onedrive"` | `True` | 원본 + 본문 → OneDrive 저장 |
| `True` | `True` | `"onedrive"` | `True` | TXT 변환 + 본문 → OneDrive 저장 |

### 4.2 본문 처리

| include_body | 결과 |
|:------------:|------|
| `True` (기본값) | 본문을 `mail_content.txt`로 저장/반환 |
| `False` | 첨부파일만 처리 (본문 제외) |

---

## 5. 사용 예시

### 5.1 배치 조회 + 로컬 저장 (기본)

```python
handler = BatchAttachmentHandler(base_directory="downloads")

result = await handler.fetch_and_save(
    user_email="user@example.com",
    message_ids=["msg_id_1", "msg_id_2", "msg_id_3"],
)
# 결과: downloads/{날짜}_{보낸사람}_{제목}/ 폴더에 저장
```

### 5.2 TXT 변환 + 로컬 저장

```python
result = await handler.fetch_and_save(
    user_email="user@example.com",
    message_ids=["msg_id_1"],
    convert_to_txt=True,
)
# 결과: PDF/DOCX/XLSX/PPTX → TXT 변환 후 저장
```

### 5.3 OneDrive 저장

```python
result = await handler.fetch_and_save(
    user_email="user@example.com",
    message_ids=["msg_id_1"],
    storage_type="onedrive",
    onedrive_folder="/Mail/Attachments",
)
# 결과: OneDrive의 /Mail/Attachments/ 폴더에 저장
```

### 5.4 TXT 변환 + OneDrive 저장

```python
result = await handler.fetch_and_save(
    user_email="user@example.com",
    message_ids=["msg_id_1"],
    storage_type="onedrive",
    onedrive_folder="/Mail/Converted",
    convert_to_txt=True,
)
```

### 5.5 TXT 변환 → 메모리 반환 (저장 안함)

```python
result = await handler.fetch_and_save(
    user_email="user@example.com",
    message_ids=["msg_id_1"],
    convert_to_txt=True,
    save_file=False,           # 저장하지 않음
)
# 결과: result["converted_contents"]에 TXT 내용이 담김
```

### 5.6 첨부파일만 (본문 제외)

```python
result = await handler.fetch_and_save(
    user_email="user@example.com",
    message_ids=["msg_id_1"],
    include_body=False,        # 본문 제외
)
# 결과: 첨부파일만 저장, mail_content.txt 생성 안됨
```

### 5.7 메타데이터만 조회 (다운로드 없음)

```python
result = await handler.fetch_metadata_only(
    user_email="user@example.com",
    message_ids=["msg_id_1", "msg_id_2"],
)
# 결과: 첨부파일 이름, 크기, contentType 등 메타정보만 반환
```

### 5.6 특정 첨부파일만 다운로드

```python
result = await handler.fetch_specific_attachments(
    user_email="user@example.com",
    attachments_info=[
        {"message_id": "msg_id_1", "attachment_id": "att_id_1"},
        {"message_id": "msg_id_2", "attachment_id": "att_id_5"},
    ],
)
```

### 5.7 Single 방식 - 첨부파일 목록 조회

```python
handler = SingleAttachmentHandler(access_token="...")

attachments = await handler.list_attachments(
    message_id="msg_id_1",
    user_id="user@example.com",
)
# 결과: [{"id": "...", "name": "file.pdf", "size": 1024, ...}, ...]
```

### 5.8 Single 방식 - 특정 첨부파일 다운로드

```python
saved_path = await handler.download_attachment(
    message_id="msg_id_1",
    attachment_id="att_id_1",
    save_path="/tmp/myfile.pdf",
    user_id="user@example.com",
)
```

---

## 6. 반환 결과 구조

### 6.1 fetch_and_save() 결과

```python
{
    "success": True,
    "total_requested": 3,
    "processed": 3,
    "skipped_duplicates": 0,
    "saved_mails": ["path/to/mail_content.txt", ...],
    "saved_attachments": ["path/to/file.pdf", ...],
    "converted_files": [
        {"original": "report.pdf", "converted": "report.txt", "path": "..."}
    ],
    "errors": [],
    "storage_type": "local",
    "convert_to_txt": False,
}
```

### 6.2 fetch_metadata_only() 결과

```python
{
    "success": True,
    "messages": [
        {
            "id": "msg_id_1",
            "subject": "제목",
            "from": {"name": "...", "address": "..."},
            "receivedDateTime": "2025-01-09T10:00:00Z",
            "hasAttachments": True,
            "attachments": [
                {"id": "att_1", "name": "file.pdf", "size": 1024, "contentType": "application/pdf"}
            ]
        }
    ],
    "total_processed": 1,
    "attachments_count": 1,
}
```

### 6.3 fetch_specific_attachments() 결과

```python
{
    "success": True,
    "total_requested": 2,
    "downloaded": 2,
    "failed": 0,
    "results": [
        {"message_id": "...", "attachment_id": "...", "file_path": "...", "success": True}
    ],
}
```

---

## 7. TXT 변환 지원 형식

| 형식 | 지원 | 라이브러리 |
|------|:----:|-----------|
| PDF | ✅ | pdfplumber |
| DOCX | ✅ | python-docx |
| XLSX | ✅ | openpyxl |
| PPTX | ✅ | python-pptx |
| HWP/HWPX | ✅ | olefile |
| TXT/CSV/JSON/XML | ✅ | 내장 |
| DOC/XLS/PPT | ❌ | 구 형식 미지원 |

**변환 실패 시**: 원본 파일로 저장 (fallback)

---

## 8. 파일 구조

```
mcp_outlook/
├── mail_attachment.py             # 핸들러 (진입점 + 오케스트레이터)
│   ├── BatchAttachmentHandler     # 배치 처리 진입점
│   │   └── _process_mail_with_options()  # 오케스트레이터 (processor 호출)
│   ├── SingleAttachmentHandler    # 개별 처리
│   └── MailMetadataManager        # 중복 관리
│
├── mail_attachment_processor.py   # 처리 로직 (순수 함수)
│   ├── process_body_content()     # 메일 본문 처리
│   ├── process_attachments()      # 첨부파일 목록 처리
│   ├── process_attachment_with_conversion()  # TXT 변환 처리
│   └── process_attachment_original()         # 원본 저장 처리
│
├── mail_attachment_storage.py     # 저장소 Backend
│   ├── StorageBackend             # 추상 기본 클래스
│   ├── LocalStorageBackend        # 로컬 저장
│   ├── OneDriveStorageBackend     # OneDrive 저장
│   ├── MailFolderManager          # 폴더/파일 관리 (LocalStorageBackend 상속)
│   └── get_storage_backend()      # 팩토리 함수
│
└── mail_attachment_converter.py   # 파일 변환기
    ├── FileConverter              # 추상 기본 클래스
    ├── PlainTextConverter         # TXT/CSV 변환
    ├── PdfConverter               # PDF 변환
    ├── WordConverter              # DOCX 변환
    ├── ExcelConverter             # XLSX 변환
    ├── PowerPointConverter        # PPTX 변환
    ├── HwpConverter               # HWP/HWPX 변환
    ├── ConversionPipeline         # 변환 파이프라인
    └── get_conversion_pipeline()  # 싱글톤 팩토리
```

### 8.1 모듈 역할 분리

| 모듈 | 역할 | 의존성 |
|------|------|--------|
| `mail_attachment.py` | 진입점, 오케스트레이션, API 조회 | storage, processor, converter |
| `mail_attachment_processor.py` | 처리 로직 (순수 함수) | storage, converter |
| `mail_attachment_storage.py` | 저장소 추상화 (Local/OneDrive) | - |
| `mail_attachment_converter.py` | 파일 형식 변환 | 외부 라이브러리 |

### 8.2 호출 흐름

```
BatchAttachmentHandler.fetch_and_save()
    └── _process_mail_with_options()  [오케스트레이터]
        ├── storage.create_folder()
        ├── processor.process_body_content()
        │   └── storage.save_mail_content()
        ├── processor.process_attachments()
        │   ├── processor.process_attachment_with_conversion()
        │   │   ├── converter.convert()
        │   │   └── storage.save_file()
        │   └── processor.process_attachment_original()
        │       └── storage.save_file()
        └── metadata_manager.add_processed_mail()
```
