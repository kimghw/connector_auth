# @mcp_service 데코레이터 / JSDoc

> **Python**: 데코레이터 사용 시 반드시 `mcp_service_decorator.py`를 import하거나 fallback 패턴을 구현해야 합니다.
> **JavaScript**: JSDoc 주석 방식으로 `@mcp_service` 태그 사용 (데코레이터 문법 불필요)

## 요약

| 항목 | 내용 |
|:-----|:-----|
| **사용 스크립트** | `mcp_service_scanner.py`, `generate_editor_config.py` |
| **사용 함수** | `scan_codebase_for_mcp_services()`, `find_jsdoc_mcp_services_in_js_file()` |
| **입력** | Python: `@mcp_service` 데코레이터, JavaScript: `@mcp_service` JSDoc 주석 |
| **출력** | `mcp_{server}/registry_{server}.json`, `editor_config.json` |

```
[Python]     @mcp_service 데코레이터 → AST 스캔 → registry/config JSON 생성
[JavaScript] @mcp_service JSDoc 주석 → 정규식 스캔 → registry/config JSON 생성
```

## 파일 위치
- **Python 데코레이터**: `mcp_editor/mcp_service_registry/mcp_service_decorator.py`
- **JavaScript 스캐너**: `mcp_editor/mcp_service_registry/mcp_service_scanner.py` (`find_jsdoc_mcp_services_in_js_file()`)

## 지원 언어

| 언어 | 확장자 | 파서 | 서비스 정의 방식 |
|:-----|:------|:-----|:--------------|
| Python | `.py` | `ast` (내장) | ✅ `@mcp_service` 데코레이터 |
| JavaScript | `.js`, `.mjs` | regex (내장) | ✅ `@mcp_service` JSDoc 주석 |
| TypeScript | `.ts`, `.tsx` | `esprima` | ✅ `@McpService` 데코레이터 |

> **참고**: JavaScript는 JSDoc 주석 방식으로 데코레이터 없이 메타데이터 정의 가능

## 참조하는 파일

### 정의 파일
| 언어 | 파일 | 상태 |
|:-----|:-----|:-----|
| Python | `mcp_service_decorator.py` | ✅ 구현됨 |
| JavaScript | JSDoc 주석 방식 (파일 불필요) | ✅ 구현됨 |

> **참고**: JavaScript는 JSDoc 주석을 사용하므로 별도 데코레이터 정의 파일 불필요

### 서비스 정의 예시 파일
| 파일 | 언어 | 용도 |
|:-----|:-----|:-----|
| `mcp_outlook/outlook_service.py` | Python | Outlook 서비스 |
| `mcp_calendar/calendar_service.py` | Python | Calendar 서비스 |
| `mcp_file_handler/file_manager.py` | Python | File Handler 서비스 |
| `AssetManagement/asset-api/services/crew.service.js` | JavaScript | 선원 관리 서비스 |

### 스캔 함수
| 파일 | 함수 | 용도 |
|:-----|:-----|:-----|
| `mcp_service_scanner.py` | `scan_codebase_for_mcp_services()` | 통합 스캔 (Python + JS) |
| `mcp_service_scanner.py` | `find_mcp_services_in_python_file()` | Python AST 파싱 |
| `mcp_service_scanner.py` | `find_jsdoc_mcp_services_in_js_file()` | JavaScript JSDoc 파싱 |
| `generate_editor_config.py` | `extract_server_name_from_py_file()` | Python server_name 추출 |
| `generate_editor_config.py` | `extract_server_name_from_js_file()` | JavaScript server_name 추출 |

### 메타데이터 활용
| 파일 | 용도 |
|:-----|:-----|
| `service_registry.py` | 서비스 레지스트리 구축 |
| `meta_registry.py` | 메타 레지스트리 관리 |
| `tool_loader.py` | 툴 정의 로딩 시 서비스 팩터 추출 |

---

## 서비스 정의 문법

### 파라미터 비교

| 파라미터 | Python | JavaScript JSDoc | TypeScript | 필수 |
|:---------|:-------|:-----------------|:-----------|:-----|
| Tool 이름 | `tool_name` | `@tool_name` | `toolName` | ✅ |
| 서버 식별자 | `server_name` | `@server_name` | `serverName` | ✅ |
| 메서드명 | `service_name` | `@service_name` | `serviceName` | 선택 (기본: 함수명) |
| 기능 설명 | `description` | `@description` | `description` | ✅ |
| 카테고리 | `category` | `@category` | `category` | 권장 |
| 태그 | `tags` | `@tags` | `tags` | 권장 |
| 파라미터 | 함수 시그니처 | `@param` | 함수 시그니처 | 자동 |
| 반환 타입 | 타입 힌트 | `@returns` | 타입 힌트 | 자동 |

### Python

```python
@mcp_service(
    tool_name="handler_mail_list",
    server_name="outlook",
    service_name="query_mail_list",
    description="메일 리스트 조회 기능",
    category="outlook_mail",
    tags=["query", "search"],
)
def query_mail_list(self, user_email: str, top: int = 50):
    ...
```

### JavaScript (JSDoc 주석)

```javascript
/**
 * @mcp_service
 * @tool_name get_crew_list
 * @server_name asset_management
 * @service_name getCrew
 * @description 전체 선원 정보 조회 (육상, 선박 전체)
 * @category crew_query
 * @tags query,search,filter
 * @param {Array<number>} [shipIds] - 선박 ID 목록으로 필터링
 * @param {string} [where] - 검색 조건 (name|ship|mobile)
 * @param {string} [query] - 검색어
 * @returns {Array<Object>} 선원 목록
 */
crewService.getCrew = async (params = {}) => {
    ...
}
```

> **JSDoc 규칙**:
> - `@mcp_service` 태그가 있어야 스캔 대상
> - `[param]` 대괄호는 optional 파라미터
> - `@tags`는 쉼표로 구분

### TypeScript (experimentalDecorators 필요)

```typescript
@McpService({
    toolName: "handler_mail_list",
    serverName: "outlook",
    serviceName: "query_mail_list",
    description: "메일 리스트 조회 기능",
    category: "outlook_mail",
    tags: ["query", "search"],
})
async function queryMailList(userEmail: string, top: number = 50) {
    ...
}
```

---

## 자동 추출 정보

### Python (런타임 데코레이터)

| 추출 항목 | 소스 |
|:---------|:-----|
| `parameters` | `inspect.signature(func)` |
| `required_parameters` | 기본값 없는 파라미터 |
| `return_type` | `get_type_hints(func)["return"]` |
| `is_async` | `inspect.iscoroutinefunction(func)` |
| `module` | `func.__module__` |
| `function` | `func.__name__` |

### JavaScript (JSDoc 파싱)

| 추출 항목 | 소스 |
|:---------|:-----|
| `parameters` | `@param {type} name - description` |
| `is_optional` | `[param]` 대괄호 여부 |
| `return_type` | `@returns {type}` |
| `is_async` | 함수 정의 `async` 키워드 |
| `function_name` | 함수 정의에서 추출 |
| `line` | JSDoc 블록 위치 |

---

## 글로벌 레지스트리

```python
MCP_SERVICE_REGISTRY: Dict[str, Dict[str, Any]] = {}
```

데코레이터가 적용된 함수는 자동으로 글로벌 레지스트리에 등록됩니다.

### 레지스트리 조회 함수

| 함수 | 용도 |
|:-----|:-----|
| `get_mcp_service_info(func_or_name)` | 특정 서비스 메타데이터 조회 |
| `list_mcp_services()` | 전체 서비스 목록 반환 |
| `generate_inputschema_from_service(name)` | JSON Schema 생성 |

---

## 데이터 흐름

```
[Python]
@mcp_service(server_name="outlook")  ← 개발자 설정
        ↓
AST 스캔 (find_mcp_services_in_python_file)
        ↓
mcp_outlook/registry_outlook.json 생성
        ↓
editor_config.json 자동 생성
        ↓
웹 에디터에서 프로필 표시

[JavaScript]
/** @mcp_service @server_name asset_management */  ← 개발자 설정
        ↓
JSDoc 스캔 (find_jsdoc_mcp_services_in_js_file)
        ↓
mcp_asset_management/registry_asset_management.json 생성
        ↓
editor_config.json 자동 생성
        ↓
웹 에디터에서 프로필 표시
```

---

## 웹 에디터 API (레지스트리 조회)

웹 에디터 UI(JavaScript)는 Flask API를 통해 파싱된 레지스트리 데이터를 조회합니다:

| JS 호출 | Python 엔드포인트 | 데이터 소스 |
|:--------|:-----------------|:-----------|
| `fetch('/api/services')` | `registry_routes.py` | `registry_{server}.json` |
| `fetch('/api/profiles')` | `profile_routes.py` | `editor_config.json` |
| `fetch('/api/services/{profile}/list')` | `registry_routes.py` | 레지스트리 스캔 결과 |

### 예시
```javascript
// 서비스 목록 조회
const response = await fetch('/api/services/outlook/list');
const services = await response.json();
// → 데코레이터에서 추출된 서비스 메타데이터
```

---


## 핵심 필드: server_name

`server_name`은 가장 중요한 필드입니다:

- **프로필 생성 기준**: `editor_config.json`의 프로필 키
- **경로 컨벤션**: `server_name="outlook"` → `../mcp_outlook`
- **레지스트리 경로**: `mcp_outlook/registry_outlook.json`
- **포트 할당**: 프로필별 순차 할당 (8001부터)

> **결론**: `server_name`만 올바르게 설정하면 나머지는 자동 처리됨

---

## JSDoc 타입 매핑

JavaScript JSDoc 타입은 JSON Schema 타입으로 변환됩니다:

| JSDoc 타입 | JSON Schema 타입 |
|:-----------|:----------------|
| `{string}` | `"string"` |
| `{number}` | `"number"` |
| `{boolean}` | `"boolean"` |
| `{Object}` | `"object"` |
| `{Array}`, `{Array<T>}` | `"array"` |
| `{*}`, `{any}` | `"any"` |

### JSDoc 함수 정의 패턴 지원

스캐너는 다음 JavaScript 함수 정의 패턴을 인식합니다:

```javascript
// 패턴 1: 객체 메서드
crewService.getCrew = async (params) => { ... }

// 패턴 2: 일반 함수
async function updateUserLicense(id, updateData) { ... }

// 패턴 3: const 함수
const getCrew = async function(params) { ... }

// 패턴 4: exports
exports.getCrew = async (params) => { ... }
```
