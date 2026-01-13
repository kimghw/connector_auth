# @mcp_service 데코레이터

> **필수**: 데코레이터 사용 시 반드시 `mcp_service_decorator.py`를 import하거나 fallback 패턴을 구현해야 합니다. 그렇지 않으면 런타임에 `NameError`가 발생합니다.

## 요약

| 항목 | 내용 |
|:-----|:-----|
| **사용 스크립트** | `mcp_service_scanner.py`, `generate_editor_config.py` |
| **사용 함수** | `scan_codebase_for_mcp_services()`, `extract_server_name_from_file()` |
| **입력** | 서비스 파일의 `@mcp_service` 데코레이터 |
| **출력** | `registry_{server}.json`, `editor_config.json` |

```
서비스 파일 (@mcp_service) → AST 스캔 → registry/config JSON 생성
```

## 파일 위치
`mcp_editor/mcp_service_registry/mcp_service_decorator.py`

## 지원 언어

| 언어 | 확장자 | 파서 | 데코레이터 지원 |
|:-----|:------|:-----|:--------------|
| Python | `.py` | `ast` (내장) | ✅ 네이티브 |
| TypeScript | `.ts`, `.tsx` | `esprima` | ✅ experimentalDecorators |
| JavaScript | `.js`, `.mjs` | `esprima` | ❌ 미지원 |

> **참고**: 순수 JavaScript는 데코레이터 문법이 없음. TypeScript 사용 권장.

## 참조하는 파일

### 데코레이터 정의
| 언어 | 파일 | 상태 |
|:-----|:-----|:-----|
| Python | `mcp_service_decorator.py` | ✅ 구현됨 |
| JavaScript | (미구현) | ❌ 필요 시 추가 |
ㄴ
> **참고**: 스캐너는 JavaScript 파싱을 지원하지만, JavaScript용 데코레이터 정의는 아직 없음

### 데코레이터 사용 (서비스 정의)
| 파일 | 용도 |
|:-----|:-----|
| `mcp_outlook/outlook_service.py` | Outlook 서비스 함수 정의 |
| `mcp_calendar/calendar_service.py` | Calendar 서비스 함수 정의 |
| `mcp_file_handler/file_manager.py` | File Handler 서비스 함수 정의 |

### 데코레이터 스캔 (AST 분석)
| 파일 | 함수 | 용도 |
|:-----|:-----|:-----|
| `mcp_service_scanner.py` | `scan_codebase_for_mcp_services()` | 코드베이스에서 데코레이터 추출 |
| `generate_editor_config.py` | `extract_server_name_from_file()` | `server_name` 추출 |
| `generate_server_mappings.py` | `extract_server_name_from_file()` | 서버 매핑 생성 |

### 메타데이터 활용
| 파일 | 용도 |
|:-----|:-----|
| `service_registry.py` | 서비스 레지스트리 구축 |
| `meta_registry.py` | 메타 레지스트리 관리 |
| `tool_loader.py` | 툴 정의 로딩 시 서비스 팩터 추출 |

---

## 데코레이터 시그니처

### 파라미터 비교

| 파라미터 | Python (snake_case) | TypeScript (camelCase) | 필수 |
|:---------|:-------------------|:-----------------------|:-----|
| Tool 이름 | `tool_name` | `toolName` | ✅ |
| 서버 식별자 | `server_name` | `serverName` | ✅ |
| 메서드명 | `service_name` | `serviceName` | ✅ |
| 기능 설명 | `description` | `description` | ✅ |
| 카테고리 | `category` | `category` | 권장 |
| 태그 | `tags` | `tags` | 권장 |
| 우선순위 | `priority` | `priority` | 선택 |
| 관련 객체 | `related_objects` | `relatedObjects` | 선택 |

> 스캐너가 TypeScript camelCase를 snake_case로 자동 변환

### Python

```python
@mcp_service(
    tool_name="handler_mail_list",
    server_name="outlook",
    service_name="query_mail_list",
    description="메일 리스트 조회 기능",
    category="outlook_mail",
    tags=["query", "search"],
    priority=5,
)
def query_mail_list(self, user_email: str, top: int = 50):
    ...
```

### TypeScript (experimentalDecorators 필요)

```typescript
@McpService({
    toolName: "handler_mail_list",
    serverName: "outlook",
    serviceName: "query_mail_list",
    description: "메일 리스트 조회 기능",
    category: "outlook_mail",
    tags: ["query", "search"],
    priority: 5,
})
async function queryMailList(userEmail: string, top: number = 50) {
    ...
}
```

> **참고**: 순수 JavaScript는 데코레이터 문법 미지원. TypeScript의 `experimentalDecorators` 옵션 필요.

---

## 자동 추출 정보

데코레이터는 함수 시그니처에서 다음을 자동 추출합니다:

| 추출 항목 | 소스 |
|:---------|:-----|
| `parameters` | `inspect.signature(func)` |
| `required_parameters` | 기본값 없는 파라미터 |
| `return_type` | `get_type_hints(func)["return"]` |
| `is_async` | `inspect.iscoroutinefunction(func)` |
| `module` | `func.__module__` |
| `function` | `func.__name__` |

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
@mcp_service(server_name="outlook")  ← 개발자 설정
        ↓
AST 스캔 (mcp_service_scanner.py)
        ↓
registry_outlook.json 생성
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
- **레지스트리 파일**: `registry_outlook.json`
- **포트 할당**: 프로필별 순차 할당 (8001부터)

> **결론**: `server_name`만 올바르게 설정하면 나머지는 자동 처리됨
