# User Query Log

> 사용자 요청 및 변경 사항 기록

---

## 2026-01-06 (2)

### Graph Mail 모듈 리팩토링 - URL 빌더 통합

**사용자 요청:**
- filter, search, expand(attachment)는 `graph_mail_url.py`로 통합
- `graph_mail_query.py`는 인증 처리 + URL로 조회하는 역할
- `graph_mail_attachment.py`는 첨부파일 processor 역할
- `graph_mail_client.py`는 조회, 후처리, 조합 역할

**변경 사항:**

#### 1. 신규 파일 생성
- `graph_mail_url.py` - URL 빌더 통합 모듈
  - `FilterBuilder`: $filter URL 파라미터 빌더
  - `SearchBuilder`: $search URL 파라미터 빌더
  - `ExpandBuilder`: $expand URL 파라미터 빌더
  - `GraphMailUrlBuilder`: 통합 URL 빌더
  - `quick_filter()`, `build_filter_query()` 편의 함수

#### 2. 기존 파일 수정
- `graph_mail_query.py`: URL 빌드 로직 제거, `GraphMailUrlBuilder` 사용
- `graph_mail_attachment.py`: `ExpandBuilder` import로 변경

#### 3. 삭제된 파일
- `graph_mail_filter.py` → `graph_mail_url.py`로 통합
- `graph_mail_search.py` → `graph_mail_url.py`로 통합
- `graph_filter_helpers.py` → `graph_mail_url.py`로 통합

**새 구조:**
```
mcp_outlook/
├── graph_mail_url.py        # URL 빌더 통합 (filter/search/expand)
├── graph_mail_query.py      # 인증 + 조회 (URL로 API 호출)
├── graph_mail_attachment.py # 첨부파일 Processor
├── graph_mail_client.py     # 통합 클라이언트 (조회+후처리+조합)
└── graph_mail_id_batch.py   # 배치 조회
```

**역할 분리:**
| 모듈 | 책임 |
|------|------|
| `graph_mail_url.py` | URL 생성만 (순수 빌더) |
| `graph_mail_query.py` | 인증 + URL로 API 호출 + 페이지네이션 |
| `graph_mail_attachment.py` | 첨부파일 다운로드/저장/메타 관리 |
| `graph_mail_client.py` | 쿼리 + 처리 조합, 고수준 API |

---

## 2026-01-06

### 1. graph_mail_attachment.py 생성
- `$batch` + `$expand=attachments`로 메일+첨부파일 한번에 조회
- 폴더명: `{YYYYMMDD}_{보낸사람}_{제목}`
- `message_id` 기반 중복 제거
- 기존 `attachment_handler.py` 삭제

### 2. 파일 삭제 및 정리
- `mail_text_processor.py` 삭제 (txt 변환은 외부 툴 사용)
- `mail_processor_handler.py` 삭제 (기능 중복)

### 3. Enum 제거
- `MailStorageOption`, `AttachmentOption`, `OutputFormat` → 문자열로 단순화
- `"skip"`, `"download"`, `"convert"` 등 직접 사용

### 현재 구조
```
graph_mail_client.py → graph_mail_attachment.py → outlook_types.py
```

---
