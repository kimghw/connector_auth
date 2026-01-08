# 사용자 시나리오 기록

## 최근 세션 기록

### 2026-01-08: YAML Single Source of Truth 리팩토링

#### 요청 사항
- `tool_definitions.py`와 `tool_definition_templates.yaml` 중복 제거
- YAML 파일을 Single Source of Truth로 통합
- 웹에디터 Save 시 YAML만 저장
- 서버 코드가 런타임에 YAML에서 직접 로드

#### 문제점 분석
- 기존: 웹에디터 Save 시 두 개 파일 생성
  - `tool_definitions.py`: LLM API용 클린 버전
  - `tool_definition_templates.yaml`: mcp_service_factors 포함
- `tool_definitions.py`의 모든 내용이 YAML에도 있어 중복됨

#### 해결 방안

**1. universal_server_template.jinja2 수정**
- `from tool_definitions import MCP_TOOLS` 제거
- `_load_mcp_tools()` 함수 추가: YAML에서 직접 로드
```python
def _load_mcp_tools() -> List[Dict[str, Any]]:
    yaml_path = Path(current_dir).parent.parent / "mcp_editor" / "mcp_{server}" / "tool_definition_templates.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data.get("tools", [])

MCP_TOOLS = _load_mcp_tools()
```

**2. tool_editor_web.py 수정**
- `tool_definitions.py` 생성 로직 제거 (라인 856-942)
- YAML만 저장하도록 변경
- 반환값 변경: `{"success": True, "saved": yaml_path}`

**3. 삭제된 파일**
- `/home/kimghw/Connector_auth/mcp_outlook/mcp_server/tool_definitions.py`
- `/home/kimghw/Connector_auth/mcp_file_handler/mcp_server/tool_definitions.py`

#### 검증 결과
- 웹에디터 Save API 테스트 ✅
  - `tool_definitions.py` 생성 안 됨 ✅
  - `tool_definition_templates.yaml` 저장 성공 (9개 도구) ✅
- 서버 재생성 테스트 ✅
  - 3개 프로토콜 (REST, STDIO, Stream) 생성 성공 ✅
- 런타임 YAML 로드 테스트 ✅
  - MCP_TOOLS: 9개 도구 로드 ✅
  - SERVICE_FACTORS: 6개 도구 추출 ✅

#### 수정된 파일
- `jinja/universal_server_template.jinja2`: YAML 런타임 로드 추가
- `mcp_editor/tool_editor_web.py`: tool_definitions.py 생성 로직 제거
- `.claude/commands/web.md`: v3.0 업데이트
- `.claude/commands/handler.md`: YAML 참조로 변경

---

### 2026-01-08: targetParam 기준 Internal/Defaults 병합 렌더링 개선

#### 요청 사항
- 핸들러에서 default(signature_defaults)와 internal을 targetParam 기준으로 **먼저 하드코딩**하여 렌더링
- 그 후 Signature(사용자 입력)가 default를 덮어쓰도록 구성

#### 문제점 분석
- 기존: `tool.signature_defaults.get(param_name, {}).get('value', {})`로 찾음
- `param_name`은 inputSchema의 property name (예: `DatePeriodFilter`)
- `signature_defaults`의 키는 factor_name이므로 **targetParam 기준 매칭이 안 됨**

#### 해결 방안

**1. generate_universal_server.py 수정**
- `object_params` 생성 시 targetParam 기준으로 매칭된 값을 미리 계산
- 새로 추가된 필드:
  - `target_param`: 서비스 메서드 파라미터명
  - `internal_defaults`: targetParam 기준 internal factor의 value
  - `signature_defaults_values`: targetParam 기준 signature_defaults factor의 value

**2. universal_server_template.jinja2 수정**
- pre-computed된 `param_info.internal_defaults`와 `param_info.signature_defaults_values` 사용
- 변수 이름 변경: `_internal_data` → `_internal_defaults`, `sig_defaults` → `_sig_defaults`
- 주석 추가: `# Pre-computed defaults by targetParam: {{ param_info.target_param }}`

#### 생성된 핸들러 코드 예시 (mail_fetch_filter)
```python
# Pre-computed defaults by targetParam: filter_params
filter_params_internal_defaults = {}
filter_params_sig_defaults = {'test_field': 'test_value'}
# Merge: Internal < Signature Defaults < Signature (user input)
filter_params_data = merge_param_data(filter_params_internal_defaults, filter_params, filter_params_sig_defaults)
```

#### 병합 우선순위
```
Internal < Signature Defaults < Signature (사용자 입력)
```

#### 검증 결과
- outlook 서버 3개 프로토콜 (REST, STDIO, Stream) 생성 성공
- `mail_fetch_filter`에서 signature_defaults 정상 적용 확인
- `mail_list_period`에서 internal args (select_params, client_filter) 정상 적용 확인

#### 수정된 파일
- `jinja/generate_universal_server.py`: object_params에 targetParam 기준 defaults 추가
- `jinja/universal_server_template.jinja2`: pre-computed values 사용하도록 수정

---

### 2026-01-07: 핸들러 지침에 따른 제너레이터/템플릿 개선

#### 요청 사항
- 핸들러 지침(handler.md)에 따라 `generate_universal_server.py`와 `universal_server_template.jinja2` 검토 및 업데이트
- signature_defaults 처리 로직 추가

#### 문제점 분석
1. **signature_defaults 미처리**: `extract_internal_args_from_tools()` 함수가 `source='internal'`만 처리하고 `source='signature_defaults'`를 무시
2. **병합 우선순위 불완전**: Signature → Signature Defaults → Internal 우선순위 미구현

#### 핸들러 파라미터 체계 정리
- **Signature**: LLM이 제공하는 사용자 입력값 (inputSchema에 정의)
- **Signature Defaults**: Signature 파라미터의 기본값 (같은 targetParam, mcp_service_factors source='signature_defaults')
- **Internal**: LLM에게 숨겨진 시스템 고정값 (다른 targetParam, mcp_service_factors source='internal')
- **중요**: Signature와 Internal은 서로 다른 targetParam을 가리키므로 겹치지 않음

#### 수정 내용

**1. generate_universal_server.py**
- `extract_service_factors_from_tools()` 함수 추가: `internal`과 `signature_defaults` 모두 처리
- `extract_internal_args_from_tools()` 함수를 레거시 호환성을 위해 유지
- `prepare_context()`에 `service_factors` 파라미터 추가
- 각 tool에 `signature_defaults`, `service_factors` 속성 추가

**2. universal_server_template.jinja2**
- `SERVICE_FACTORS` 변수 추가 (internal + signature_defaults 구조)
- `merge_param_data()` 함수 개선: 세 번째 인자로 `signature_defaults` 받음
- `get_signature_defaults()`, `apply_signature_defaults()`, `merge_with_priority()` 헬퍼 함수 추가
- object_params 처리 시 signature_defaults 적용

#### 병합 우선순위
```
merge_param_data(internal_data, runtime_data, signature_defaults)
→ 최종값 = internal < signature_defaults < runtime (사용자 입력)
```

#### 검증 결과
- outlook 서버 3개 프로토콜 (REST, STDIO, Stream) 생성 성공
- `mail_fetch_filter`에서 signature_defaults 적용 확인:
  ```python
  filter_params_data = merge_param_data(filter_params_internal_data, filter_params, {'test_field': 'test_value'})
  ```
- Python 문법 검사 통과

#### 수정된 파일
- `jinja/generate_universal_server.py`
- `jinja/universal_server_template.jinja2`

---

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

*마지막 업데이트: 2026-01-08*
