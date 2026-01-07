# 사용자 시나리오 기록

## 최근 세션 기록

### 2026-01-07: MCP Tool-Service 매핑 수정

#### 요청 사항
1. `tool_definitions.py`에 `mcp_service.name` 필드가 누락되어 서버에서 `MailService` 메서드를 찾지 못하는 오류 수정
2. `select_params` internal arguments가 제대로 적용되는지 검증

#### 해결된 문제
- **오류**: `'MailService' object has no attribute 'mail_list_period'`
- **원인**: 웹에디터 Save 시 `tool_definitions.py`에 `mcp_service.name` 필드가 포함되지 않음
- **수정 파일**: `mcp_editor/tool_editor_web.py` (lines 787-796)
  - `mcp_service` 필드가 있을 때 `name` 값만 추출하여 `tool_definitions.py`에 포함하도록 수정

#### 검증 완료
- `mail_list_period` → `query_mail_list()` 매핑 정상 동작
- `mail_attachment_meta` → `fetch_attachments_metadata()` 매핑 정상 동작
- `select_params` internal arguments 정상 적용 (API 응답에서 지정된 필드만 반환)

---

### 2025-01-07: 첨부파일 처리 기능 구현

#### 요청 사항
1. `batch_and_attachment` 메서드에 메타데이터만 조회하는 옵션 추가
2. `GraphAttachmentHandler` 메서드 통합 (3개 → 2개)
3. `fetch_attachments_metadata`, `download_attachments` 통합 함수 구현
4. Facade 패턴 적용

#### 구현 완료 항목
- 메타데이터 전용 조회 기능 (`fetch_attachments_metadata`)
- 통합 다운로드 함수 (다형성 지원 - 메일 ID 또는 첨부파일 ID 쌍)
- Facade 패턴 적용 (`outlook_service.py`)
- 실제 데이터 테스트 완료

#### 관련 파일
- `mcp_outlook/graph_mail_attachment.py` (+240 lines)
- `mcp_outlook/graph_mail_client.py` (+118 lines)
- `mcp_outlook/outlook_service.py` (+78 lines)

---

## 이전 세션 요약

### MCP 서버 아키텍처
- Jinja2 템플릿 기반 서버 생성 시스템
- 3가지 프로토콜 지원: REST, STDIO, Stream
- `tool_definition_templates.py` → `tool_definitions.py` 생성 파이프라인

### 핵심 파일 관계
```
tool_definition_templates.py (mcp_service_factors 포함)
        ↓
generate_universal_server.py
        ↓
server_rest.py / server_stdio.py / server_stream.py
```

### 파라미터 체계
- **Signature**: LLM이 직접 제공하는 파라미터
- **Signature Defaults**: LLM에게 보이지만 기본값 제공
- **Internal**: 시스템 고정값 (LLM에게 숨김)

---

*마지막 업데이트: 2026-01-07*
