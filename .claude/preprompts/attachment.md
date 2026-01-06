# 첨부파일 다운로드 관련 파일 정리

## 변경된 파일 목록 (Git 기준)

### 1. **mcp_outlook/graph_mail_attachment.py** (+240 lines)
첨부파일 처리의 핵심 모듈

#### 주요 클래스
- `MailFolderManager`: 메일별 폴더 생성 및 파일 저장 관리
- `MailMetadataManager`: 메타정보 저장 및 중복 제거
- `GraphAttachmentHandler`: 배치 첨부파일 처리
- `AttachmentHandler`: 개별 첨부파일 처리

#### 핵심 메서드
```python
# GraphAttachmentHandler 클래스
- fetch_metadata_only()      # 메타데이터만 조회 (다운로드 없음)
- fetch_and_save()           # 메일 ID로 모든 첨부파일 다운로드
- fetch_specific_attachments() # 특정 첨부파일만 선택적 다운로드

# AttachmentHandler 클래스  
- list_attachments()         # 특정 메일의 첨부파일 목록 조회
- get_attachment()           # 특정 첨부파일 상세 정보 조회
- download_attachment()      # 개별 첨부파일 다운로드
```

### 2. **mcp_outlook/graph_mail_client.py** (+118 lines)
통합 메일 처리 클라이언트

#### 새로 추가된 통합 함수
```python
async def fetch_attachments_metadata(
    user_email: str,
    message_ids: List[str],
    select_params: Optional[SelectParams] = None
) -> Dict[str, Any]
# 메일과 첨부파일의 메타데이터만 조회

async def download_attachments(
    user_email: str,
    target: Union[List[str], List[Dict[str, str]]],
    save_directory: str = "downloads",
    skip_duplicates: bool = True,
    select_params: Optional[SelectParams] = None
) -> Dict[str, Any]
# 입력 타입에 따라 자동 처리:
# - 메일 ID 리스트: 모든 첨부파일 다운로드
# - 첨부파일 ID 쌍: 특정 첨부파일만 다운로드
```

### 3. **mcp_outlook/outlook_service.py** (+78 lines)
MCP 서비스 Facade 레이어

#### MCP 서비스 함수
```python
@mcp_service(tool_name="handle_attachments_metadata")
async def fetch_attachments_metadata()
# GraphMailClient.fetch_attachments_metadata() 위임

@mcp_service(tool_name="handle_download_attachments")
async def download_attachments()
# GraphMailClient.download_attachments() 위임
```

## 파일 처리 흐름

```
1. MCP Tools Layer
   └── outlook_service.py (Facade)
       └── graph_mail_client.py (통합 인터페이스)
           └── graph_mail_attachment.py (실제 처리 로직)
               ├── MailFolderManager (폴더/파일 관리)
               ├── MailMetadataManager (메타데이터 관리)
               └── AttachmentHandler (Graph API 통신)
```

## 주요 기능

### 1. 메타데이터 조회 (다운로드 없음)
- 메일 본문(body) 포함
- 첨부파일 정보(이름, 크기, 타입) 포함
- $expand=attachments 파라미터 사용

### 2. 첨부파일 다운로드
- **전체 다운로드**: 메일 ID 리스트로 해당 메일의 모든 첨부파일
- **선택적 다운로드**: message_id + attachment_id 쌍으로 특정 첨부파일만
- 폴더 구조: `{날짜}_{발신자}_{제목}/`
- 메일 본문도 `mail_content.txt`로 저장

### 3. 중복 처리
- `mail_metadata.json` 파일로 처리 이력 관리
- skip_duplicates 옵션으로 중복 다운로드 방지

## 관련 타입 정의
```python
# 입력 타입
Union[List[str], List[Dict[str, str]]]  # 메일 ID 또는 첨부파일 ID 쌍

# SelectParams
Optional[SelectParams]  # 필드 선택 파라미터

# 반환 타입
Dict[str, Any]  # 처리 결과 (status, value, errors 등)
```

## 테스트 파일
- `test_attachment_functions.py`: 함수 존재 및 시그니처 확인
- `test_real_attachments.py`: 실제 메일 데이터로 테스트

## 저장 구조 예시
```
downloads/
└── 20251231_한국항해항만학회_[제목]/
    ├── mail_content.txt     # 메일 본문
    └── attachment.gif       # 첨부파일
```

---
*최종 업데이트: 2025-01-07*
*변경 규모: 3개 파일, 총 +436 lines*
