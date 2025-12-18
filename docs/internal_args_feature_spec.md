# MCP Tool Internal Args 기능 명세서

---

## 📊 구현 진행 상황 요약

> **최종 업데이트**: 2025-12-17 (Phase 1-3 구현 완료 + 버그 수정 10건)

### 전체 진행률

| Phase | 설명 | 상태 | 진행률 |
|-------|------|------|--------|
| **Phase 1** | Jinja 생성기 수정 | ✅ 완료 | 100% |
| **Phase 2** | 웹 에디터 백엔드 | ✅ 완료 | 100% |
| **Phase 3** | 웹 에디터 프론트엔드 | ✅ 완료 | 100% |
| **Phase 4** | 통합 테스트 | ⏳ 미착수 | 0% |

### 완료된 항목 ✅

1. **Phase 1: Jinja 생성기** (2025-12-17)
   - `load_internal_args()` 함수 추가
   - `find_internal_args_file()` 함수 추가
   - `collect_all_param_types()` 함수 추가
   - 템플릿에 Internal args 코드 생성 블록 추가
   - `generate_server()` 함수에 internal_args 지원 추가

2. **Phase 2: 웹 에디터 백엔드** (2025-12-17)
   - `resolve_paths()`에 `internal_args_path` 추가
   - `editor_config.json`에 `internal_args_path` 경로 추가
   - `GET /api/tools` 응답에 `internal_args`, `file_mtimes` 필드 추가
   - `load_internal_args()` 함수 추가
   - `get_file_mtimes()` 함수 추가
   - `GET/POST /api/internal-args` API 엔드포인트 추가
   - `PUT /api/internal-args/{tool_name}` API 엔드포인트 추가
   - `POST /api/tools/save-all` 원자적 저장 API 추가
   - `backup_file()` 함수로 3개 파일 백업 지원
   - `cleanup_old_backups()` 함수로 백업 관리

3. **Phase 3: 웹 에디터 프론트엔드** (2025-12-17)
   - `internalArgs`, `fileMtimes` 전역 변수 추가
   - `loadTools()`에서 internal_args, file_mtimes 로드
   - Destination 선택 UI (To Signature / To Internal) 구현
   - Internal value JSON 입력 필드 구현
   - `setPropertyDestination()` 함수 구현
   - `updateInternalArgValue()` 함수 구현
   - `saveTools()`에서 `/api/tools/save-all` API 사용
   - 파일 충돌 감지 및 경고 메시지

4. **Bug Fixes (Code Review)** (2025-12-17)
   - **Issue 1**: `setPropertyDestination()`에서 `inputSchema.properties`에서 제거/복원 로직 수정
     - Signature → Internal 전환 시 `inputSchema.properties`에서 실제 제거
     - `required` 배열에서도 제거
     - `original_schema`, `was_required` 메타데이터 저장
     - Internal → Signature 전환 시 `original_schema`로 복원
   - **Issue 2**: Jinja 생성기에서 `internal_args`를 `call_params`에 병합
     - `generate_outlook_server.py`에서 internal_args를 call_params에 자동 추가
     - 생성된 서버 코드에서 internal args가 service method에 전달됨
   - **Issue 3**: Internal args 삭제 시 정리 로직 추가
     - `DELETE /api/tools/{index}` 호출 시 해당 tool의 internal_args도 삭제
     - `POST /api/tools/save-all` 호출 시 orphaned internal_args 자동 정리
   - **Issue 4**: 백업 정책 정리
     - `save_tool_definitions()`에 `skip_backup` 파라미터 추가
     - `save_all_definitions()`에서 호출 시 중복 백업 방지
   - **Issue 5**: Internal args 유효성 검사 추가
     - `type` 필드 필수 검증
     - 잘못된 형식 검증 (dict 형태 확인)
     - 검증 실패 시 400 오류 반환
   - **Issue 6**: Internal args UI 가시성 수정
     - `renderToolEditor()`가 `inputSchema.properties`와 `internalArgs` 모두 표시하도록 수정
     - Internal로 이동된 프로퍼티가 UI에서 사라지지 않고 계속 편집 가능
     - `original_schema` 또는 `internalArgs` 정보로 프로퍼티 정보 표시
   - **Issue 7**: Falsy default 값 보존 수정
     - `setPropertyDestination()`에서 `||` 연산자 대신 `!== undefined` 사용
     - `false`, `0`, `""` 같은 falsy 값이 `{}` 또는 `null`로 대체되지 않음
   - **Issue 8**: Internal 프로퍼티 편집 시 inputSchema 재노출 방지
     - `updatePropertyField()`, `updatePropertyEnum()`, `toggleEnum()`, `toggleRequired()` 수정
     - Internal 프로퍼티 편집 시 `internalArgs[].original_schema` 업데이트
     - `inputSchema.properties`에 다시 생성되지 않도록 방지
   - **Issue 9**: Internal 프로퍼티 삭제 시 internalArgs 정리
     - `removeProperty()`에서 `internalArgs`도 함께 삭제
     - 빈 tool entry 자동 정리
   - **Issue 10**: Internal 프로퍼티 type 변경이 생성기에 반영되지 않음
     - `updatePropertyField()`에서 `type` 변경 시 `internalArgs[].type` 업데이트
     - baseModel 선택기에서 Internal 프로퍼티 처리 추가
     - `internalArgs[].type`이 Jinja 생성기가 사용하는 값이므로 동기화 필수

### 미구현 항목 ⏳

1. **Phase 4: 통합 테스트**
   - End-to-End 테스트 시나리오 실행
   - Signature → Internal 전환 테스트
   - Internal → Signature 복원 테스트
   - 서버 생성 후 실행 테스트

### 다음 작업 권장 순서

```
1. Phase 4: 통합 테스트 실행
   - 웹 에디터에서 Destination 전환 테스트
   - 저장 후 tool_internal_args.json 확인
   - Jinja 생성기로 서버 생성 테스트
   - 생성된 서버 코드 검증
```

---

## 1. 배경 및 문제점

### 1.1 현재 상황

현재 MCP 웹 에디터 시스템은 다음과 같은 구조로 동작합니다:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     웹 에디터 (tool_editor_web.py)                       │
│                                                                          │
│  save_tool_definitions() 함수가 동시에 2개 파일 생성:                     │
│                                                                          │
│  1. tool_definitions.py                                                  │
│     - mcp_service 메타데이터 제거된 클린 버전                             │
│     - 경로: mcp_outlook/mcp_server/tool_definitions.py                  │
│     - 용도: MCP 서버에서 직접 사용 (tools/list 응답)                      │
│                                                                          │
│  2. tool_definition_templates.py                                         │
│     - mcp_service 메타데이터 포함                                        │
│     - 경로: mcp_editor/outlook/tool_definition_templates.py             │
│     - 용도: Jinja 생성기의 입력 파일                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Jinja 생성기 (generate_outlook_server.py)                   │
│                                                                          │
│  tool_definition_templates.py 읽기                                       │
│                          ↓                                               │
│  outlook_server_template.jinja2 렌더링                                   │
│                          ↓                                               │
│  server.py (또는 server_generated.py) 생성                               │
└─────────────────────────────────────────────────────────────────────────┘
```

**문제점**: 모든 파라미터가 MCP 시그니처(inputSchema)에 노출됩니다.

예를 들어, `handle_query_filter` 툴의 경우:
- `user_email` - LLM이 전달해야 함 (필요)
- `filter` - LLM이 전달해야 함 (필요)
- `select` - 어떤 필드를 조회할지 (내부 설정으로 충분)
- `client_filter` - 클라이언트 필터링 조건 (내부 설정으로 충분)

`select`, `client_filter` 같은 파라미터는 LLM이 매번 전달할 필요가 없습니다.
이러한 파라미터들은 **사전에 설정된 기본값**으로 처리하는 것이 효율적입니다.

### 1.2 현재 파일 구조

| 파일 | 경로 | 용도 | 웹 에디터 연동 |
|------|------|------|----------------|
| `tool_definitions.py` | `mcp_outlook/mcp_server/` | MCP 서버에서 사용 (클린 버전) | O (자동 생성) |
| `tool_definition_templates.py` | `mcp_editor/outlook/` | Jinja 생성기 입력 (메타데이터 포함) | O (자동 생성) |
| `tool_internal_args.json` | `mcp_editor/outlook/` | 내부 파라미터 기본값 | X (수동 관리) |
| `server.py` | `mcp_outlook/mcp_server/` | 실제 MCP 서버 코드 | O (Jinja로 생성) |

**핵심 문제**:
1. `tool_internal_args.json`이 웹 에디터와 연동되지 않아 수동으로 관리해야 함
2. `tool_definitions.py`의 inputSchema에 모든 파라미터가 노출됨 (Internal 파라미터 분리 안됨)
3. Jinja 생성기가 `tool_internal_args.json`을 사용하지 않음

---

## 2. 목표

### 2.1 주요 목표

1. **파라미터 분리 관리**: MCP 시그니처에 노출할 파라미터와 내부에서 처리할 파라미터를 분리
2. **웹 에디터 통합**: 웹 에디터에서 두 종류의 파라미터를 모두 편집 가능하게 함
3. **Jinja 템플릿 연동**: 서버 코드 생성 시 internal args가 자동으로 반영되도록 함

### 2.2 기대 효과

| 항목 | Before | After |
|------|--------|-------|
| LLM 호출 복잡도 | 모든 파라미터 전달 필요 | 필수 파라미터만 전달 |
| 파라미터 관리 | 수동 JSON 편집 | 웹 UI로 편집 |
| 서버 코드 생성 | internal args 미반영 | 자동 반영 |
| 설정 변경 | 코드 수정 필요 | 웹 에디터에서 변경 |

### 2.3 최종 목표 흐름

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      웹 에디터 (tool_editor_web.py)                      │
│                                                                          │
│  Property 편집 시 Destination 선택:                                      │
│    [To Signature] - MCP에 노출할 파라미터                                │
│    [To Internal]  - 함수 내부에서 처리할 파라미터                         │
│                                                                          │
│  save_tool_definitions() 수정:                                          │
│    - Signature 파라미터 → tool_definitions.py + tool_definition_templates.py │
│    - Internal 파라미터 → tool_internal_args.json                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│tool_definitions  │ │tool_definition_  │ │tool_internal_    │
│.py               │ │templates.py      │ │args.json         │
│                  │ │                  │ │                  │
│Signature만 포함  │ │Signature +       │ │Internal 파라미터 │
│(MCP 서버 사용)   │ │mcp_service 메타  │ │+ 기본값          │
└──────────────────┘ └──────────────────┘ └──────────────────┘
                              │                   │
                              └─────────┬─────────┘
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 generate_outlook_server.py                              │
│  - tool_definition_templates.py 로드 (Signature 파라미터)               │
│  - tool_internal_args.json 로드 (Internal 파라미터)                     │
│  - 두 데이터를 템플릿 컨텍스트로 전달                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 outlook_server_template.jinja2                          │
│  - Signature 파라미터: args에서 추출하는 코드 생성                        │
│  - Internal 파라미터: 기본값으로 객체 생성하는 코드 생성                   │
└─────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         server.py (생성됨)                               │
│  - MCP tools/list: Signature 파라미터만 노출                             │
│  - 함수 내부: Internal 파라미터는 기본값으로 자동 적용                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 핵심 규칙 정의

### 3.1 Internal 파라미터의 타입/호출 정보 관리

**문제**: inputSchema에서 Internal 파라미터를 제거하면 Jinja 생성기가 타입 정보를 잃어버림

**해결 규칙**:

1. **tool_internal_args.json에 완전한 메타데이터 저장**
   ```json
   {
     "handle_query_filter": {
       "select": {
         "type": "SelectParamsExpanded",     // 타입 클래스명 (필수)
         "param_name": "select",              // 함수 파라미터명 (필수)
         "description": "조회할 필드 선택",
         "is_optional": true,                 // Optional 여부
         "value": { "id": true, ... }         // 기본값 (필수)
       }
     }
   }
   ```

2. **Jinja 생성기의 데이터 병합 순서**
   ```
   1. tool_definition_templates.py 로드 → Signature 파라미터
   2. tool_internal_args.json 로드 → Internal 파라미터
   3. 각 툴별로 두 소스를 병합하여 완전한 파라미터 목록 구성
   4. 템플릿 렌더링 시 병합된 데이터 전달
   ```

3. **생성 코드에서의 구분**
   - Signature 파라미터: `args.get("param_name")` 또는 `args["param_name"]`
   - Internal 파라미터: 하드코딩된 기본값으로 객체 생성

### 3.2 Signature ↔ Internal 전환 시 규칙

**문제**: 전환 시 required 목록, 기본값, 메타데이터가 손실될 수 있음

**전환 규칙**:

| 전환 방향 | 처리 항목 | 규칙 |
|----------|----------|------|
| Signature → Internal | required 배열 | 해당 파라미터를 required에서 제거 |
| Signature → Internal | inputSchema.properties | 해당 프로퍼티 제거 |
| Signature → Internal | 타입 정보 | tool_internal_args.json에 type 필드로 보존 |
| Signature → Internal | 기본값 | 사용자가 웹 UI에서 value 입력 필수 |
| Internal → Signature | required 배열 | is_optional=false면 required에 추가 |
| Internal → Signature | inputSchema.properties | tool_internal_args.json의 타입 정보로 복원 |
| Internal → Signature | 기본값 | inputSchema.properties.default로 이동 (선택적) |

**데이터 보존을 위한 구조**:
```json
// tool_internal_args.json - 복원에 필요한 모든 정보 저장
{
  "handle_query_filter": {
    "select": {
      "type": "SelectParamsExpanded",
      "param_name": "select",
      "original_schema": {           // 원본 스키마 보존 (복원용)
        "type": "object",
        "description": "조회할 필드 선택",
        "properties": { ... }
      },
      "was_required": false,         // 원래 required였는지 여부
      "value": { ... }
    }
  }
}
```

### 3.3 Internal Args 타입의 Import 규칙

**문제**: Internal args에서만 사용하는 타입이 import에서 누락됨

**해결 규칙**:

1. **generate_outlook_server.py에서 타입 수집**
   ```python
   def collect_all_param_types(tools, internal_args):
       """Signature + Internal 모든 파라미터에서 타입 수집"""
       types = set()

       # Signature 파라미터에서 수집
       for tool in tools:
           for prop in tool.get('inputSchema', {}).get('properties', {}).values():
               if 'baseModel' in prop:
                   types.add(prop['baseModel'])

       # Internal 파라미터에서 수집
       for tool_name, params in internal_args.items():
           for param_info in params.values():
               if 'type' in param_info:
                   types.add(param_info['type'])

       return types
   ```

2. **템플릿에서 동적 import 생성**
   ```jinja2
   from outlook_types import {{ all_param_types | join(', ') }}
   ```

3. **타입 매핑 테이블** (outlook_types.py에 정의된 타입만 허용)
   ```python
   ALLOWED_TYPES = {
       'FilterParams', 'ExcludeParams', 'SelectParams',
       'SelectParamsExpanded', 'EmailMessage', ...
   }
   ```

### 3.4 API 저장/동기화 전략

**문제**: 두 파일(templates.py, internal_args.json)이 어긋날 수 있음

**API 동작 규칙 및 우선순위**:

| API | 동작 | 동기화 범위 | 우선순위 |
|-----|------|------------|---------|
| `POST /api/tools/save-all` | **권장**: 통합 저장 | 3개 파일 원자적 저장 | 1 (Primary) |
| `POST /api/tools` | 기존 호환용 | tool_definitions.py + templates.py | 2 |
| `POST /api/internal-args` | 단독 저장 (비권장) | internal_args.json만 | 3 |
| `PUT /api/internal-args/{tool}` | 부분 업데이트 | 해당 툴만 | 4 |

**API 호출 시나리오 및 처리**:

| 시나리오 | 동작 | 결과 |
|----------|------|------|
| `save-all` 성공 | 3개 파일 모두 저장 | 일관성 보장 |
| `save-all` 중 templates 저장 실패 | 롤백 | 모든 파일 원복 |
| `save-all` 중 internal_args 저장 실패 | 롤백 | 모든 파일 원복 |
| `POST /api/tools`만 호출 | 저장 후 경고 반환 | `{"warning": "internal_args not updated"}` |
| `POST /api/internal-args`만 호출 | 저장 후 경고 반환 | `{"warning": "tool_definitions not updated"}` |

**충돌 해결 규칙**:

1. **동시 수정 감지**
   - 저장 전 파일의 mtime 체크
   - 로드 시점과 저장 시점의 mtime이 다르면 충돌 경고
   ```python
   if current_mtime != loaded_mtime:
       return {"error": "File was modified externally", "action": "reload_required"}
   ```

2. **삭제 규칙**
   - Internal → Signature 전환 시: `tool_internal_args.json`에서 해당 파라미터 제거
   - 툴 삭제 시: `tool_internal_args.json`에서 해당 툴 전체 제거
   - 고아 데이터 정리: `save-all` 시 templates에 없는 툴은 internal_args에서도 제거

**동기화 전략**:

1. **백업 타이밍**
   - 저장 전 항상 기존 파일 백업 (timestamped)
   - tool_definitions.py, templates.py, internal_args.json 모두 백업
   - 백업 파일명: `{filename}_{YYYYMMDD_HHMMSS}.bak`

2. **원자적 저장 (트랜잭션 방식)**
   ```python
   def save_all_definitions(tools_data, internal_args, paths):
       """3개 파일을 트랜잭션처럼 저장"""
       backups = {}
       saved_files = []

       try:
           # 1. 모든 백업 생성 (저장 전)
           backups = create_backups(paths)

           # 2. 순차 저장 (실패 시 즉시 롤백)
           save_tool_definitions(tools_data, paths)
           saved_files.append("tool_definitions")

           save_templates(tools_data, paths)
           saved_files.append("templates")

           save_internal_args(internal_args, paths)
           saved_files.append("internal_args")

           # 3. 백업 정리 (성공 시)
           cleanup_old_backups(paths, keep_count=10)

           return {"success": True, "saved": saved_files}

       except Exception as e:
           # 4. 실패 시 롤백
           restore_from_backups(backups)
           return {
               "error": str(e),
               "rolled_back": saved_files,
               "action": "all_files_restored"
           }
   ```

3. **파일 버전 일관성 체크**
   ```python
   def check_consistency(paths):
       """파일들의 수정 시간 비교하여 불일치 감지"""
       templates_mtime = os.path.getmtime(paths["template_path"])
       internal_mtime = os.path.getmtime(paths["internal_args_path"])
       definitions_mtime = os.path.getmtime(paths["tool_path"])

       # 5초 이상 차이나면 경고
       max_diff = max(
           abs(templates_mtime - internal_mtime),
           abs(templates_mtime - definitions_mtime)
       )
       if max_diff > 5:
           return {
               "warning": "Files may be out of sync",
               "recommendation": "Use POST /api/tools/save-all to synchronize"
           }
       return {"status": "consistent"}
   ```

4. **부분 저장 API 사용 시 경고**
   ```python
   @app.route('/api/internal-args', methods=['POST'])
   def save_internal_args_only():
       # 저장 수행
       result = save_internal_args_file(data, paths)

       # 일관성 체크 후 경고 추가
       consistency = check_consistency(paths)
       if "warning" in consistency:
           result["warning"] = "internal_args saved but tool_definitions may be out of sync"
           result["recommendation"] = "Consider using POST /api/tools/save-all"

       return jsonify(result)
   ```

### 3.5 null/빈 값 처리 및 검증 규칙

**문제**: Internal args의 value가 null이거나 빈 경우의 처리 방법

**value 허용 규칙** (변경됨 - null 허용):

| 케이스 | UI 허용 | 저장 시 | 생성 코드 | 의미 |
|--------|---------|---------|----------|------|
| `value: null` | O | 허용 | `param = None` | 파라미터 전달 안함 |
| `value: {}` | O | 허용 | `TypeClass()` | 기본 생성자 |
| `value: {"key": "val"}` | O | 허용 | `TypeClass(key="val")` | 구체적 값 |
| `value: {"key": null}` | O | 허용 | `TypeClass(key=None)` | 특정 키만 None |
| `type` 필드 누락 | X | 거부 | - | 오류 |
| `value` 필드 자체 누락 | X | 거부 | - | 오류 |

**생성 코드 분기 로직**:
```jinja2
{%- for arg_name, arg_info in tool.internal_args.items() %}
{%- if arg_info.value is none %}
# {{ arg_name }}: None - 파라미터 전달 안함
{{ arg_name }}_params = None
{%- elif arg_info.value == {} %}
# {{ arg_name }}: 빈 객체 - 기본 생성자 사용
{{ arg_name }}_params = {{ arg_info.type }}()
{%- else %}
# {{ arg_name }}: 기본값 있음
{{ arg_name }}_params = {{ arg_info.type }}(**{{ arg_info.value | tojson }})
{%- endif %}
{%- endfor %}
```

**웹 UI 검증**:
```javascript
function validateInternalArg(argInfo) {
    const errors = [];
    const warnings = [];

    // type 필수
    if (!argInfo.type || argInfo.type.trim() === '') {
        errors.push('type is required');
    }

    // value 필드 존재 확인 (null은 허용, undefined는 불가)
    if (argInfo.value === undefined) {
        errors.push('value field is required (use null for no default)');
    }

    // null 사용 시 경고 (권장하지 않음)
    if (argInfo.value === null) {
        warnings.push('value is null - parameter will not be passed to function');
    }

    // JSON 유효성 (문자열인 경우)
    if (typeof argInfo.value === 'string') {
        try {
            JSON.parse(argInfo.value);
        } catch (e) {
            errors.push('value must be valid JSON');
        }
    }

    return { errors, warnings };
}
```

### 3.6 기존 데이터 마이그레이션

**현재 상황**: 기존 `tool_internal_args.json`에 `value: null`이 포함된 데이터 존재

**기존 데이터 예시** (마이그레이션 대상):
```json
// mcp_editor/outlook/tool_internal_args.json
{
  "handle_query_search": {
    "client_filter": {
      "type": "ExcludeParams",
      "value": null           // ← 기존 데이터
    }
  }
}
```

**마이그레이션 전략**:

| 방식 | 설명 | 권장 |
|------|------|------|
| A. null 허용 | value: null을 유효한 값으로 인정 (위 규칙 적용) | O (채택) |
| B. 자동 변환 | null → {} 로 자동 변환 후 저장 | X |
| C. 수동 마이그레이션 | 사용자가 직접 수정 | X |

**채택된 방식: A. null 허용**

이유:
1. 기존 데이터와의 호환성 유지
2. `value: null`은 "이 파라미터는 내부적으로 None으로 처리"라는 의미로 유효
3. 생성된 코드에서 `param = None`으로 처리 가능

**마이그레이션 작업** (선택적):

기존 데이터를 새 스키마에 맞게 보강할 경우:
```python
def migrate_internal_args(internal_args: dict) -> dict:
    """기존 데이터에 누락된 필드 추가"""
    for tool_name, params in internal_args.items():
        for param_name, param_info in params.items():
            # param_name 필드 추가 (없으면)
            if "param_name" not in param_info:
                param_info["param_name"] = param_name

            # is_optional 필드 추가 (없으면 기본값 true)
            if "is_optional" not in param_info:
                param_info["is_optional"] = True

    return internal_args
```

**웹 에디터 로드 시 자동 보강**:
- 기존 데이터 로드 시 누락된 필드는 기본값으로 채움
- 저장 시 새 스키마 형식으로 저장
- 기존 데이터 손상 없이 점진적 마이그레이션

---

## 4. 요구사항

### 4.1 기능 요구사항

#### FR-01: 웹 에디터 UI
- [ ] ⏳ Property 편집 시 "Destination" 선택 옵션 제공
  - `To Signature`: MCP 시그니처에 노출 (기본값)
  - `To Internal`: 함수 내부에서 처리
- [ ] ⏳ Internal 선택 시 기본값(value) 설정 UI 제공
- [ ] ⏳ 기본값은 JSON 형식으로 입력
- [ ] ⏳ Internal args 검증: type 필수, value null 불가 (빈 객체 {} 허용)
- [ ] ⏳ Signature ↔ Internal 전환 시 경고 메시지 표시

#### FR-02: API 엔드포인트
- [ ] ⏳ `GET /api/internal-args?profile={profile}`: Internal args 조회
- [ ] ⏳ `POST /api/internal-args?profile={profile}`: Internal args 전체 교체
- [ ] ⏳ `PUT /api/internal-args/{tool_name}?profile={profile}`: 특정 툴 부분 병합
- [ ] ⏳ `POST /api/tools/save-all?profile={profile}`: 3개 파일 원자적 저장 (새 API)

#### FR-02.5: 웹 에디터 초기 로드 (템플릿 + Internal Args 동시 로드)
- [ ] ⏳ `GET /api/tools` 호출 시 `tool_definition_templates.py`와 함께 `tool_internal_args.json`도 로드
- [ ] ⏳ 프론트엔드에 통합된 데이터 반환 (Signature + Internal 파라미터 모두 포함)
- [ ] ⏳ Internal args 파일이 없으면 빈 객체 `{}` 반환 (오류 없이 정상 동작)
- [ ] ⏳ 로드 시 파일 mtime 기록하여 저장 시 충돌 감지용으로 사용

**로드 시 데이터 병합 규칙**:
```
GET /api/tools 응답 형식:
{
  "tools": [...],                    // tool_definition_templates.py에서 로드
  "internal_args": {...},            // tool_internal_args.json에서 로드
  "profile": "outlook",
  "file_mtimes": {                   // 충돌 감지용 타임스탬프
    "templates": 1702800000.0,
    "internal_args": 1702800000.0,
    "definitions": 1702800000.0
  }
}
```

#### FR-03: 저장 로직
- [ ] ⏳ 저장 시 Signature 파라미터와 Internal 파라미터 분리
- [x] ✅ Signature → `tool_definitions.py` + `tool_definition_templates.py` (기존 구현됨)
- [ ] ⏳ Internal → `tool_internal_args.json`
- [x] ✅ 저장 전 tool_definitions.py 백업 (기존 구현됨)
- [ ] ⏳ 저장 전 3개 파일 모두 백업 (timestamped) - internal_args.json 백업 추가 필요
- [ ] ⏳ Signature → Internal 전환 시 original_schema, was_required 보존
- [ ] ⏳ Internal → Signature 전환 시 original_schema로 복원

**백업 정책 (tool_internal_args.json 포함)**:
```
백업 대상 파일:
1. tool_definitions.py        → backups/tool_definitions_{timestamp}.py.bak
2. tool_definition_templates.py → backups/tool_definition_templates_{timestamp}.py.bak
3. tool_internal_args.json    → backups/tool_internal_args_{timestamp}.json.bak

백업 위치:
- mcp_editor/{profile}/backups/  (프로필별 백업 디렉토리)

백업 파일명 형식:
- {original_filename}_{YYYYMMDD_HHMMSS}.bak

⚠️ 중요: 동일 저장 세션 = 동일 타임스탬프
- 3개 파일이 함께 저장될 때 동일한 타임스탬프 사용
- 이를 통해 어떤 파일들이 함께 저장되었는지 추적 가능
- 예시 (동일 저장 세션):
  - tool_definitions_20241217_143022.py.bak
  - tool_definition_templates_20241217_143022.py.bak
  - tool_internal_args_20241217_143022.json.bak
  → 같은 타임스탬프 = 같은 저장 세션에서 백업됨

백업 보존 정책:
- 최근 10개 세션 백업만 유지 (세션 = 동일 타임스탬프 그룹)
- 이전 백업 자동 삭제
```

**저장 순서 (트랜잭션 방식)**:
```python
def save_all_with_backup(tools_data, internal_args, paths, loaded_mtimes=None):
    """3개 파일을 원자적으로 저장 (백업 포함)"""
    backup_dir = os.path.join(os.path.dirname(paths["template_path"]), "backups")

    # ⭐ 동일 타임스탬프 생성 (한 번만!)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. 모든 파일 백업 (동일 타임스탬프 사용)
    backups = {
        "definitions": backup_file(paths["tool_path"], backup_dir, timestamp),
        "templates": backup_file(paths["template_path"], backup_dir, timestamp),
        "internal_args": backup_file(paths["internal_args_path"], backup_dir, timestamp)
    }

    # 2. 파일 충돌 체크 (mtime 비교)
    if loaded_mtimes and not check_mtime_consistency(paths, loaded_mtimes):
        restore_from_backups(backups)
        return {"error": "File was modified externally", "action": "reload_required"}

    # 3. 순차 저장 (실패 시 롤백)
    try:
        save_tool_definitions(tools_data, paths)
        save_templates(tools_data, paths)
        save_internal_args(internal_args, paths)

        # 4. 오래된 백업 정리
        cleanup_old_backups(backup_dir, keep_count=10)

        return {"success": True, "backups": backups, "timestamp": timestamp}
    except Exception as e:
        restore_from_backups(backups)
        return {"error": str(e), "rolled_back": True}

def backup_file(file_path: str, backup_dir: str, timestamp: str) -> Optional[str]:
    """단일 파일 백업 (외부에서 전달된 타임스탬프 사용)"""
    if not os.path.exists(file_path):
        return None

    os.makedirs(backup_dir, exist_ok=True)
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}_{timestamp}.bak")

    shutil.copy2(file_path, backup_path)
    return backup_path
```

#### FR-04: Jinja 생성기
- [ ] ⏳ `tool_internal_args.json` 로드 기능 (`load_internal_args()`)
- [ ] ⏳ tools_path 기반 자동 경로 탐색 (`find_internal_args_file()`)
- [ ] ⏳ Signature + Internal 파라미터 병합하여 완전한 목록 구성
- [ ] ⏳ 모든 파라미터 타입 수집 (Signature + Internal) (`collect_all_param_types()`)
- [ ] ⏳ 템플릿 컨텍스트에 internal_args, all_param_types 전달

#### FR-05: Jinja 템플릿
- [ ] ⏳ Internal args를 함수 내부에서 처리하는 코드 생성
- [ ] ⏳ 타입 클래스 인스턴스 자동 생성 (예: `SelectParams(**value)`)
- [ ] ⏳ 빈 객체({}) 처리: 기본 생성자 호출
- [ ] ⏳ Internal 타입도 import 문에 포함
- [ ] ⏳ Signature/Internal 파라미터 구분 주석 생성

### 4.2 비기능 요구사항

#### NFR-01: 하위 호환성
- [x] ✅ 기존 `tool_internal_args.json` 형식 유지 (파일 존재함)
- [ ] ⏳ internal_args 없는 툴도 정상 동작

#### NFR-02: 사용성
- [ ] ⏳ 웹 UI에서 직관적인 조작
- [ ] ⏳ 변경 사항 실시간 미리보기 (선택적)

#### NFR-03: 안정성
- [x] ✅ 저장 전 자동 백업 (tool_definitions.py만 - 확장 필요)
- [ ] ⏳ JSON 유효성 검사

---

## 5. 데이터 구조

### 5.1 tool_internal_args.json 스키마

**기본 스키마** (새로 생성되는 Internal 파라미터):
```json
{
  "{tool_name}": {
    "{param_name}": {
      "type": "string",              // [필수] 타입 클래스명 (예: SelectParams, ExcludeParams)
      "param_name": "string",        // [필수] 함수 파라미터명 (key와 동일하게 유지)
      "description": "string",       // [권장] 파라미터 설명
      "is_optional": true,           // [필수] Optional 여부 (기본: true)
      "value": {}                    // [필수] 기본값 (JSON 객체, null 허용 - 아래 규칙 참조)
    }
  }
}
```

**확장 스키마** (Signature → Internal 전환 시, 복원용 메타데이터 포함):
```json
{
  "{tool_name}": {
    "{param_name}": {
      "type": "string",
      "param_name": "string",
      "description": "string",
      "is_optional": true,
      "value": {},
      "original_schema": {           // [전환 시 자동 생성] 원본 inputSchema 보존
        "type": "object",
        "description": "...",
        "properties": { ... }
      },
      "was_required": false          // [전환 시 자동 생성] 원래 required였는지 여부
    }
  }
}
```

**필드 설명**:
| 필드 | 필수 | 설명 |
|------|------|------|
| `type` | O | 타입 클래스명 (outlook_types.py에 정의된 클래스) |
| `param_name` | O | 함수 파라미터명 (보통 key와 동일) |
| `description` | - | 파라미터 설명 |
| `is_optional` | O | true면 함수 호출 시 생략 가능 |
| `value` | O | 기본값 (null, {}, 또는 구체적인 값) |
| `original_schema` | 전환 시 | Signature → Internal 전환 시 원본 스키마 보존 |
| `was_required` | 전환 시 | Signature에서 required였는지 여부 (복원용) |

### 5.2 예시

```json
{
  "handle_query_filter": {
    "select": {
      "type": "SelectParamsExpanded",
      "description": "조회할 필드 선택 (true인 필드만 반환)",
      "value": {
        "id": true,
        "subject": true,
        "from": true,
        "receivedDateTime": true,
        "hasAttachments": true,
        "importance": true,
        "bodyPreview": true,
        "body": false
      }
    },
    "client_filter": {
      "type": "ExcludeParams",
      "description": "클라이언트 측 필터링 조건",
      "value": {
        "exclude_subject_keywords": []
      }
    }
  }
}
```

### 5.3 생성될 서버 코드 예시

**Before** (모든 파라미터가 args에서 추출):
```python
async def handle_query_filter(args: Dict[str, Any]) -> Dict[str, Any]:
    user_email = args["user_email"]
    filter_params = FilterParams(**args.get("filter", {}))
    select_params = SelectParams(**args.get("select", {}))  # LLM이 전달해야 함
    client_filter_params = ExcludeParams(**args.get("client_filter", {}))  # LLM이 전달해야 함
    # ...
```

**After** (Internal args는 기본값 사용):
```python
async def handle_query_filter(args: Dict[str, Any]) -> Dict[str, Any]:
    user_email = args["user_email"]
    filter_params = FilterParams(**args.get("filter", {}))

    # Internal Args (웹 에디터에서 설정한 기본값)
    select_params = SelectParamsExpanded(**{
        "id": True, "subject": True, "from": True,
        "receivedDateTime": True, "hasAttachments": True,
        "importance": True, "bodyPreview": True, "body": False
    })
    client_filter_params = ExcludeParams(**{
        "exclude_subject_keywords": []
    })
    # ...
```

---

## 6. 작업 범위

### 6.1 수정 대상 파일

| 파일 | 수정 내용 |
|------|----------|
| `jinja/generate_outlook_server.py` | internal_args 로드 및 전달 로직 추가 |
| `jinja/outlook_server_template.jinja2` | internal args 처리 Jinja 코드 추가 |
| `mcp_editor/tool_editor_web.py` | API 엔드포인트 및 저장 로직 추가, **resolve_paths 수정** |
| `mcp_editor/templates/tool_editor.html` | Destination 선택 UI 추가 |

**resolve_paths 수정 필수 사항**:
```python
def resolve_paths(profile_conf: dict) -> dict:
    """프로필 설정에서 파일 경로 추출"""
    return {
        "tool_path": profile_conf.get("tool_path"),
        "template_path": profile_conf.get("template_path"),
        "internal_args_path": profile_conf.get("internal_args_path"),  # 추가 필수!
        # ... 기타 경로
    }
```

**프로필 설정 파일 (`editor_config.json`) 업데이트**:
```json
{
  "profiles": {
    "outlook": {
      "tool_path": "mcp_outlook/mcp_server/tool_definitions.py",
      "template_path": "mcp_editor/outlook/tool_definition_templates.py",
      "internal_args_path": "mcp_editor/outlook/tool_internal_args.json"  // 추가 필수!
    }
  }
}
```

### 6.2 신규 생성 파일

| 파일 | 용도 |
|------|------|
| `mcp_editor/{profile}/tool_internal_args.json` | 각 프로필별 internal args (이미 존재할 수 있음) |

### 6.3 작업 순서 및 단계별 테스트

> **범례**: ✅ 완료 | ⏳ 미구현 | 🔧 부분 구현

#### Phase 1: Jinja 생성기 수정 ✅ (완료)

**1.1 `generate_outlook_server.py` - internal_args 로드 추가**

| 수정 내용 | 상태 | 테스트 항목 |
|----------|------|------------|
| `load_internal_args()` 함수 추가 | ✅ | JSON 파일 로드 성공 확인 |
| `find_internal_args_file()` 함수 추가 | ✅ | tools_path 기반 자동 경로 탐색 확인 |
| `collect_all_param_types()` 함수 추가 | ✅ | Signature + Internal 타입 모두 수집 확인 |
| `generate_server()` 함수 수정 | ✅ | internal_args 로드 및 템플릿 전달 확인 |

```bash
# 테스트 명령어
cd /home/kimghw/Connector_auth/jinja
python -c "
from generate_outlook_server import load_internal_args, find_internal_args_file
path = find_internal_args_file('../mcp_editor/outlook/tool_definition_templates.py')
print(f'Found: {path}')
args = load_internal_args(path)
print(f'Loaded {len(args)} tools')
"
```

**1.2 `outlook_server_template.jinja2` - internal args 처리 로직**

| 수정 내용 | 상태 | 테스트 항목 |
|----------|------|------------|
| Internal args 코드 생성 블록 추가 | ✅ | 생성된 코드에 하드코딩된 기본값 확인 |
| 타입 import 동적 생성 | ✅ | Internal 타입도 import에 포함 확인 |
| Signature/Internal 구분 주석 | ✅ | 주석으로 구분 표시 확인 |

```bash
# 테스트 명령어
cd /home/kimghw/Connector_auth/jinja
python generate_server.py \
  --tools ../mcp_editor/outlook/tool_definition_templates.py \
  --output /tmp/test_server.py

# 생성된 파일 검증
grep -A 5 "Internal Args" /tmp/test_server.py
grep "SelectParamsExpanded" /tmp/test_server.py
```

---

#### Phase 2: 웹 에디터 백엔드 수정 ✅ (완료)

**2.0 `tool_editor_web.py` - 템플릿 로드 시 Internal Args 동시 로드 (핵심)**

> **목표**: 웹 에디터가 `tool_definition_templates.py`를 로드할 때 `tool_internal_args.json`도 함께 로드

| 수정 내용 | 상태 | 테스트 항목 |
|----------|------|------------|
| `resolve_paths()`에 `internal_args_path` 추가 | ✅ | 경로 정상 반환 확인 |
| `load_internal_args()` 함수 추가 | ✅ | JSON 파일 로드 성공 확인 |
| `GET /api/tools` 응답에 `internal_args` 필드 추가 | ✅ | 응답에 internal_args 포함 확인 |
| `GET /api/tools` 응답에 `file_mtimes` 필드 추가 | ✅ | mtime 정보 포함 확인 |
| Internal args 파일 없을 시 빈 객체 반환 | ✅ | 오류 없이 `{}` 반환 확인 |

```python
# tool_editor_web.py 수정 예시

def load_internal_args(paths: dict) -> dict:
    """Internal args JSON 파일 로드"""
    internal_args_path = paths.get("internal_args_path")
    if not internal_args_path or not os.path.exists(internal_args_path):
        return {}
    try:
        with open(internal_args_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load internal_args: {e}")
        return {}

def get_file_mtimes(paths: dict) -> dict:
    """파일들의 mtime 수집 (충돌 감지용)"""
    mtimes = {}
    for key in ["tool_path", "template_path", "internal_args_path"]:
        path = paths.get(key)
        if path and os.path.exists(path):
            mtimes[key.replace("_path", "")] = os.path.getmtime(path)
    return mtimes

@app.route('/api/tools', methods=['GET'])
def get_tools():
    """API endpoint to get current tool definitions + internal args"""
    profile = request.args.get("profile")
    profile_conf = get_profile_config(profile)
    paths = resolve_paths(profile_conf)

    # 1. 템플릿 로드
    tools = load_tool_definitions(paths)
    if isinstance(tools, dict) and "error" in tools:
        return jsonify(tools), 500

    # 2. Internal args 로드 (동시에!)
    internal_args = load_internal_args(paths)

    # 3. 파일 mtime 수집
    file_mtimes = get_file_mtimes(paths)

    actual_profile = profile or list_profile_names()[0] if list_profile_names() else "default"
    return jsonify({
        "tools": tools,
        "internal_args": internal_args,  # 추가!
        "profile": actual_profile,
        "file_mtimes": file_mtimes         # 추가!
    })
```

```bash
# 테스트 명령어
curl http://localhost:8091/api/tools?profile=outlook | jq '.internal_args'
curl http://localhost:8091/api/tools?profile=outlook | jq '.file_mtimes'
```

**2.1 `tool_editor_web.py` - API 엔드포인트 추가**

| 수정 내용 | 상태 | 테스트 항목 |
|----------|------|------------|
| `GET /api/internal-args` | ✅ | JSON 응답 확인 |
| `POST /api/internal-args` | ✅ | 저장 후 파일 변경 확인 |
| `PUT /api/internal-args/{tool}` | ✅ | 특정 툴만 업데이트 확인 |
| `POST /api/tools/save-all` | ✅ | 3개 파일 원자적 저장 확인 |

```bash
# 테스트 명령어 (웹 에디터 실행 후)
# GET 테스트
curl http://localhost:8091/api/internal-args?profile=outlook | jq .

# POST 테스트
curl -X POST http://localhost:8091/api/internal-args?profile=outlook \
  -H "Content-Type: application/json" \
  -d '{"handle_query_filter": {"select": {"type": "SelectParams", "value": {}}}}' | jq .

# 파일 변경 확인
cat mcp_editor/outlook/tool_internal_args.json | jq .
```

**2.2 `tool_editor_web.py` - 저장 로직 (Internal Args 백업 포함)**

| 수정 내용 | 상태 | 테스트 항목 |
|----------|------|------------|
| `save_tool_definitions()` 수정 | ✅ | Signature만 .py에 저장 |
| `save_internal_args()` 함수 추가 | ✅ | Internal만 .json에 저장 확인 |
| **`tool_internal_args.json` 백업** | ✅ | 저장 전 백업 파일 생성 확인 |
| 3개 파일 모두 백업 (`backup_file()`) | ✅ | definitions, templates, internal_args 모두 백업 |
| `cleanup_old_backups()` 함수 | ✅ | 오래된 백업 자동 정리 (최근 10개 유지) |

```python
# 백업 함수 예시
def backup_file(file_path: str, backup_dir: str, timestamp: str) -> Optional[str]:
    """파일 백업 생성 (동일 타임스탬프 사용)"""
    if not os.path.exists(file_path):
        return None

    os.makedirs(backup_dir, exist_ok=True)
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}_{timestamp}.bak")

    shutil.copy2(file_path, backup_path)
    return backup_path

def save_all_definitions_with_backup(tools_data, internal_args, paths):
    """3개 파일 원자적 저장 (백업 포함)"""
    backup_dir = os.path.join(os.path.dirname(paths["template_path"]), "backups")

    # ⭐ 동일 타임스탬프 생성 (3개 파일이 같은 세션에서 백업됨을 표시)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. 백업 생성 (동일 타임스탬프 사용!)
    backups = {
        "definitions": backup_file(paths["tool_path"], backup_dir, timestamp),
        "templates": backup_file(paths["template_path"], backup_dir, timestamp),
        "internal_args": backup_file(paths["internal_args_path"], backup_dir, timestamp)
    }

    try:
        # 2. 저장 수행
        save_tool_definitions(tools_data, paths)
        save_templates(tools_data, paths)
        save_internal_args(internal_args, paths)

        # 3. 오래된 백업 정리
        cleanup_old_backups(backup_dir, keep_count=10)

        return {"success": True, "backups": backups, "timestamp": timestamp}
    except Exception as e:
        # 4. 실패 시 롤백
        restore_from_backups(backups)
        return {"error": str(e), "rolled_back": True}
```

```bash
# 테스트: property를 Internal로 이동 후 저장
# 1. 웹 UI에서 select를 Internal로 변경
# 2. 저장 버튼 클릭
# 3. 결과 확인:

# tool_definitions.py에서 select 제거 확인
grep -c '"select"' mcp_outlook/mcp_server/tool_definitions.py

# tool_internal_args.json에 select 추가 확인
jq '.handle_query_filter.select' mcp_editor/outlook/tool_internal_args.json

# 백업 파일 확인 (3개 파일 모두!)
ls -la mcp_editor/outlook/backups/
# 예상 출력:
# tool_definitions_20241217_143022.py.bak
# tool_definition_templates_20241217_143022.py.bak
# tool_internal_args_20241217_143022.json.bak   <-- 추가됨
```

---

#### Phase 3: 웹 에디터 프론트엔드 수정 ✅ (완료)

**3.1 `tool_editor.html` - UI 수정**

| 수정 내용 | 상태 | 테스트 항목 |
|----------|------|------------|
| `internalArgs`, `fileMtimes` 전역 변수 | ✅ | 변수 선언 및 초기화 |
| `loadTools()`에서 internal_args 로드 | ✅ | API 응답에서 데이터 파싱 |
| Destination 라디오 버튼 추가 | ✅ | UI에 선택 옵션 표시 확인 |
| Internal value JSON 입력 필드 | ✅ | JSON 입력 필드 동작 확인 |
| `setPropertyDestination()` 함수 | ✅ | Signature ↔ Internal 전환 |
| `updateInternalArgValue()` 함수 | ✅ | Internal value 업데이트 |
| `saveTools()`에서 save-all API 사용 | ✅ | 원자적 저장 및 충돌 감지 |

```
# 수동 UI 테스트 체크리스트
[ ] 웹 에디터 접속 (http://localhost:8091)
[ ] 툴 선택 → Property 편집
[ ] Destination 드롭다운 표시 확인
[ ] "To Internal" 선택 시 value 입력 필드 표시
[ ] 빈 type으로 저장 시 오류 메시지
[ ] null value로 저장 시 오류 메시지
[ ] {} (빈 객체)는 저장 가능 확인
```

---

#### Phase 4: 통합 테스트 ⏳ (미착수)

**4.1 End-to-End 테스트**

| 시나리오 | 상태 | 예상 결과 |
|----------|------|----------|
| Signature → Internal 전환 | ⏳ | inputSchema에서 제거, JSON에 추가 |
| Internal → Signature 복원 | ⏳ | inputSchema에 복원, JSON에서 제거 |
| 서버 생성 후 실행 | ⏳ | Internal args가 함수 내부에 적용 |
| MCP tools/list 호출 | ⏳ | Internal 파라미터 비노출 |

```bash
# End-to-End 테스트 스크립트
#!/bin/bash
set -e

echo "=== Phase 4: End-to-End Test ==="

# 1. 서버 생성
echo "1. Generating server..."
cd /home/kimghw/Connector_auth/jinja
python generate_server.py \
  --tools ../mcp_editor/outlook/tool_definition_templates.py \
  --output ../mcp_outlook/mcp_server/server_generated.py

# 2. Internal args 확인
echo "2. Checking internal args in generated code..."
grep -c "Internal Args" ../mcp_outlook/mcp_server/server_generated.py || true

# 3. 서버 실행 (백그라운드)
echo "3. Starting server..."
cd ../mcp_outlook/mcp_server
python server_generated.py &
SERVER_PID=$!
sleep 3

# 4. tools/list 호출
echo "4. Calling tools/list..."
curl -s -X POST http://localhost:3000 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | jq '.result.tools[0].inputSchema.properties | keys'

# 5. 정리
echo "5. Cleanup..."
kill $SERVER_PID 2>/dev/null || true

echo "=== Test Complete ==="
```

**4.2 파일 일관성 테스트**

```bash
# 파일 수정 시간 비교
echo "=== File Consistency Check ==="
ls -la mcp_editor/outlook/tool_definition_templates.py
ls -la mcp_editor/outlook/tool_internal_args.json
ls -la mcp_outlook/mcp_server/tool_definitions.py

# 수정 시간 차이 5초 이내 확인
```

---

## 7. 용어 정의

| 용어 | 정의 |
|------|------|
| Signature Parameter | MCP inputSchema에 노출되어 LLM이 전달하는 파라미터 |
| Internal Parameter | 함수 내부에서 기본값으로 처리되는 파라미터 (LLM에 비노출) |
| tool_definitions.py | MCP 서버에서 사용하는 클린 버전 (mcp_service 메타 제거) |
| tool_definition_templates.py | Jinja 생성기 입력용 (mcp_service 메타 포함) |
| tool_internal_args.json | Internal 파라미터와 기본값을 정의하는 JSON 파일 |

---

## 8. 참고 파일

- 현재 internal args 예시: `mcp_editor/outlook/tool_internal_args.json`
- 웹 에디터 서버: `mcp_editor/tool_editor_web.py`
- Jinja 생성기: `jinja/generate_outlook_server.py`
- 서버 템플릿: `jinja/outlook_server_template.jinja2`
- 에디터 UI: `mcp_editor/templates/tool_editor.html`
