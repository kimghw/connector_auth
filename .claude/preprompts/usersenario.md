# 사용자 시나리오 기록

## 최근 세션 기록

### 2026-01-07: MCP 핸들러 전체 테스트 완료

#### 요청 사항
- MCP Outlook 서버 핸들러 전체 테스트
- 파라미터 처리 검증 (Signature, Defaults, Internal)
- client_filter를 통한 수신 후 필터링 테스트

#### 테스트 결과

| 항목 | 결과 | 비고 |
|------|------|------|
| 서버 시작 (REST 8001) | ✅ 성공 | uvicorn 정상 구동 |
| 도구 목록 조회 | ✅ 성공 | 9개 도구 등록 확인 |
| mail_list_period | ✅ 성공 | 24개 메일 조회 (2026-01-01~07) |
| mail_list_keyword | ✅ 성공 | 키워드 검색 정상 동작 |
| mail_fetch_search | ✅ 성공 | 검색 모드 동작 확인 |
| mail_attachment_meta | ✅ 성공 | 첨부파일 메타정보 조회 |
| client_filter (수신 후 필터링) | ✅ 성공 | block@krs.co.kr 제외: 24→9개 |

#### 파라미터 처리 검증
- **Signature 파라미터**: DatePeriodFilter 정상 전달 ✅
- **Internal 파라미터 (select_params)**: id, subject, sender, bodyPreview, hasAttachments, receivedDateTime, internetMessageId 필드 정상 적용 ✅
- **targetParam 매핑**: DatePeriodFilter → filter_params 정상 ✅
- **client_filter (수신 후 필터링)**: exclude_sender_address 정상 동작 ✅

#### 수정된 파일
- `mcp_outlook/graph_mail_query.py`: `_apply_client_side_filter` 함수 - ExcludeParams 전체 필드 지원 추가
- `mcp_outlook/mcp_server/server_rest.py`: `handle_mail_fetch_filter` 함수 - client_filter 파라미터 추가
- `mcp_outlook/outlook_service.py`: `fetch_filter` 함수 - client_filter 파라미터 추가

#### 파라미터 구조
- **exclude_params**: Graph API `$filter`에 적용 (서버 측 필터링)
- **client_filter**: 메일 수신 후 클라이언트 측 필터링 (`_apply_client_side_filter`)

#### 등록된 도구 목록
1. `mail_list_period` - 기간별 메일 목록 조회
2. `mail_list_keyword` - 키워드로 메일 검색
3. `mail_query_if_emaidID` - 메일 ID로 상세 조회
4. `mail_attachment_meta` - 첨부파일 메타정보 조회
5. `mail_attachment_download` - 첨부파일 다운로드
6. `mail_fetch_filter` - 필터 조건으로 메일 조회
7. `mail_fetch_search` - 키워드 검색 (본문 포함)
8. `mail_process_with_download` - 메일 조회 및 첨부파일 다운로드
9. `mail_query_url` - Graph API URL 직접 호출

---

### 2026-01-07: inputSchema default 값 동기화 문제 해결

#### 요청 사항
- 웹 에디터에서 설정한 `inputSchema.properties.default` 값이 `tool_definitions.py`에 반영되지 않는 문제 해결

#### 문제 원인
- **위치**: `mcp_editor/tool_editor_web.py` - `save_tool_definitions()` 함수 (라인 778-781)
- **원인**: `remove_defaults()` 함수가 `tool_definitions.py` 생성 시 모든 default 값을 의도적으로 제거
- **영향**: `server_rest.py`의 `apply_schema_defaults()` 함수가 default 값을 읽을 수 없음

#### 해결 방법
- `remove_defaults()` 함수 호출 제거
- 이제 웹 에디터에서 저장 시 default 값이 `tool_definitions.py`에 유지됨

#### 수정된 파일
- `mcp_editor/tool_editor_web.py` (라인 778-784)

#### 관련 구조 (두 단계 기본값 처리)
```
1단계: apply_schema_defaults() - inputSchema.properties.default에서 동적 적용 (우선)
2단계: 핸들러 함수 하드코딩 - mcp_service.parameters.default에서 생성 시 결정 (폴백)
```

#### 검증 완료
- `mail_attachment_download` 도구에서 `save_directory: 'downloadsssss'`, `skip_duplicates: False` 기본값 적용 확인

---

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
