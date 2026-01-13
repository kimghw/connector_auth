# 레지스트리 서버 데이터 흐름

## 웹 에디터에서의 사용

### 사용 목적 (2가지)

1. **서비스 목록 드롭다운 표시** - 도구 편집 시 연결할 서비스 선택
2. **저장 시 signature/parameters 보강** - tool_definition_templates.yaml에 서비스 메타데이터 추가

### 사용 흐름 1: 서비스 목록 표시

```
registry_outlook.json
         │
         ▼
GET /api/mcp-services (registry_routes.py)
         │
         ▼
웹 에디터 UI: mcp_service 드롭다운
         │
         ▼
사용자가 서비스 선택 (예: query_mail_list)
```

### 사용 흐름 2: 저장 시 보강

```
웹 에디터에서 도구 저장
         │
         ▼
tool_saver.py:save_tool_definitions()
         │
         ▼
service_registry.py:load_services_for_server()
         │
         ▼
registry_outlook.json에서 signature/parameters 읽기
         │
         ▼
tool_definition_templates.yaml에 mcp_service 정보 추가
    - signature: "user_email: str, filter_params: Optional[FilterParams]..."
    - parameters: [{name, type, is_optional, default, class_name}, ...]
```

### 관련 코드

| 파일 | 함수 | 역할 |
|------|------|------|
| `registry_routes.py` | `get_mcp_services()` | 서비스 목록 API |
| `service_registry.py` | `load_services_for_server()` | 저장 시 메타데이터 로드 |
| `tool_saver.py` | `save_tool_definitions()` | registry 정보로 YAML 보강 |
| `tool_editor_tools.js` | `loadMcpServices()` | API 호출하여 UI에 표시 |

---

## 요약

| 항목 | 내용 |
|------|------|
| **생성 스크립트** | `mcp_service_scanner.py` |
| **생성 함수** | `export_services_to_json(base_dir, server_name, output_dir)` |
| **출력 파일** | `registry_{server}.json` |
| **호출 시점** | 웹 에디터 시작 시 `scan_all_registries()` 자동 호출 |
| **API 엔드포인트** | `GET /api/mcp-services`, `GET /api/registry` |

### 참조 스크립트

| 스크립트 | 함수/메서드 | 용도 |
|----------|-------------|------|
| `service_registry.py` | `load_services_for_server()` | 서비스 메타데이터 로드 |
| `service_registry.py` | `scan_all_registries()` | 전체 프로필 스캔 |
| `registry_routes.py` | `get_mcp_services()` | API 응답 생성 |
| `registry_routes.py` | `get_registry()` | 레지스트리 파일 직접 반환 |
| `tool_loader.py` | `load_mcp_service_factors()` | 서비스 팩터 추출 |

### 지원 언어 및 패턴

| 언어 | 확장자 | 서비스 정의 패턴 | 파서 |
|------|--------|-----------------|------|
| Python | `.py` | `@mcp_service` 데코레이터 | `ast` (내장) |
| JavaScript | `.js`, `.mjs` | `server.tool()` 패턴 | regex (내장) |
| TypeScript | `.ts`, `.tsx` | `@McpService` 데코레이터 | `esprima` (선택) |

**JavaScript server.tool() 패턴** (MCP SDK):
```javascript
server.tool(
    'search_ships',                           // tool_name
    '선박을 검색합니다.',                       // description
    {                                          // Zod 스키마
        name: z.string().optional().describe('선박 이름'),
        imo: z.string().optional()
    },
    async (args) => { ... }                   // handler
);
```

**주의사항**:
- JavaScript `server.tool()` 패턴: **esprima 불필요** (regex 기반 파싱)
- TypeScript 데코레이터 패턴: `pip install esprima` 필요
- `esprima` 미설치 시 → 데코레이터 스킵, server.tool()은 정상 작동

---

## registry_{server}.json 구조

```
{
  "version": "1.0",                       ← 레지스트리 포맷 버전
  "generated_at": "2026-01-13T...",       ← 생성 시간 (ISO datetime)
  "server_name": "outlook",               ← 서버 이름
  "services": {                           ← 서비스별 메타데이터
    "query_mail_list": {
      "service_name": "query_mail_list",
      "handler": {
        "class_name": "MailService",      ← 클래스명
        "instance": "mail_service",       ← 인스턴스 변수명 (snake_case)
        "method": "query_mail_list",      ← 호출할 메서드명
        "is_async": true,                 ← 비동기 함수 여부
        "file": "/path/to/service.py",    ← 소스 파일 절대 경로
        "line": 64                        ← 함수 정의 라인 번호
      },
      "signature": "user_email: str, filter_params: Optional[FilterParams] = None",
      "parameters": [
        {
          "name": "user_email",           ← 파라미터 이름
          "type": "str",                  ← JSON Schema 호환 타입
          "is_optional": false,           ← Optional 여부 (false = 필수)
          "default": null,                ← 기본값
          "has_default": false            ← 기본값 존재 여부
        },
        {
          "name": "filter_params",
          "type": "object",               ← 클래스 타입은 "object"
          "class_name": "FilterParams",   ← 원본 클래스 이름
          "is_optional": true,            ← Optional 여부 (true = 선택)
          "default": null,
          "has_default": true
        }
      ],
      "metadata": {
        "tool_name": "handler_mail_list", ← MCP 도구 이름
        "server_name": "outlook",         ← 서버 식별자
        "category": "outlook_mail",       ← 카테고리
        "tags": ["query", "search"],      ← 태그 목록
        "priority": 5,                    ← 우선순위
        "description": "메일 리스트 조회"  ← 기능 설명
      }
    }
  }
}
```

> **제거된 필드**:
> - `is_required`: `is_optional`의 반대이므로 중복
> - `module_path`: `file`에서 추출 가능하므로 중복

---

## API 엔드포인트

**파일**: `tool_editor_core/routes/registry_routes.py`

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/registry` | GET | 특정 프로필의 레지스트리 파일 조회 |
| `/api/mcp-services` | GET | MCP 서비스 목록 및 상세 정보 |

### GET /api/mcp-services 응답

```json
{
  "services": ["service1", "service2"],
  "services_with_signatures": [
    {
      "name": "service1",
      "parameters": [...],
      "signature": "param1: str, ...",
      "class_name": "ClassName",
      "file": "/path/to/service.py"
    }
  ],
  "groups": {},
  "is_merged": false,
  "source_profiles": []
}
```

---

## 데이터 흐름

```
[빌드타임]

소스 코드 (@mcp_service 데코레이터)
         │
         ▼
웹에디터 시작
         │
         ▼
scan_all_registries()
         │
         ▼
mcp_service_scanner.py (AST 스캔)
         │
         ▼
registry_{server}.json 생성
         │
         ▼
GET /api/mcp-services
         │
         ▼
JSON 응답 → 웹 UI 표시
```

---

## type vs class_name 분리

### 배경
기존에는 `type` 필드에 클래스 이름이 직접 저장됨 (예: `"type": "FilterParams"`)
이는 JSON Schema 타입과 혼동되어 일관성 문제 발생

### 변경 후 구조

| 상황 | type | class_name |
|------|------|------------|
| 기본 타입 | `str`, `int`, `bool` | (없음) |
| 제네릭 타입 | `List[str]`, `Dict[str, Any]` | (없음) |
| 커스텀 클래스 | `object` | `FilterParams` |

### 판별 로직 (`mcp_service_scanner.py:_is_class_type`)

```python
def _is_class_type(type_str: str) -> bool:
    # PascalCase이고 제네릭 아닌 경우 = 클래스
    if not type_str[0].isupper():
        return False
    generic_prefixes = ("List[", "Dict[", "Union[", "Optional[", ...)
    if any(type_str.startswith(prefix) for prefix in generic_prefixes):
        return False
    return True
```

---

## 핵심 개념

### Handler vs Metadata

| 구분 | Handler | Metadata |
|------|---------|----------|
| 역할 | 실행 라우팅 정보 | 분류/설명 정보 |
| 예시 | class_name, method, file | category, tags, description |
| 사용 | 런타임 호출 | UI 표시, 검색 필터링 |

---

## JavaScript 서비스 스캔

### server.tool() 패턴 스캔

**함수**: `mcp_service_scanner.py:find_server_tool_calls_in_js_file()`

regex 기반으로 `server.tool()` 호출을 파싱하여 서비스 정보 추출.

### 추출되는 정보

```javascript
server.tool(
    'search_ships',                // → service_name, tool_name
    '선박 검색',                    // → description
    {
        name: z.string().optional().describe('이름'),
        shipType: z.enum(['tanker', 'cargo'])
    },                             // → parameters (Zod 스키마에서 추출)
    async (args) => { ... }        // → is_async: true
);
```

### Zod 타입 매핑

| Zod 메서드 | 추출 정보 |
|-----------|----------|
| `z.string()` | type: "string" |
| `z.number()` | type: "number" |
| `z.boolean()` | type: "boolean" |
| `z.enum(['a', 'b'])` | type: "string", enum: ["a", "b"] |
| `.optional()` | is_optional: true |
| `.default(value)` | default: value, has_default: true |
| `.describe('text')` | description: "text" |
| `.min(n)` | minimum: n |
| `.max(n)` | maximum: n |

### JavaScript registry 출력 구조

```json
{
  "version": "1.0",
  "generated_at": "2026-01-13T...",
  "server_name": "asset",
  "language": "javascript",
  "services": {
    "search_ships": {
      "service_name": "search_ships",
      "handler": {
        "class_name": null,
        "method": "search_ships",
        "is_async": true,
        "file": "/path/to/ship-tools.js",
        "line": 15
      },
      "signature": "name: string, imo: string, shipType: string",
      "parameters": [
        {
          "name": "name",
          "type": "string",
          "is_optional": true,
          "description": "선박 이름"
        },
        {
          "name": "shipType",
          "type": "string",
          "is_optional": true,
          "enum": ["tanker", "cargo"]
        }
      ],
      "metadata": {
        "tool_name": "search_ships",
        "description": "선박 검색"
      },
      "pattern": "server.tool"
    }
  }
}
```

### 언어 자동 감지

`export_services_to_json()`에서 프로젝트 언어를 자동 감지:

```python
# 스캔된 서비스에서 language 필드 확인
has_js_services = any(s.get("language") == "javascript" for s in services.values())
has_py_services = any(s.get("language") == "python" for s in services.values())

# JavaScript만 있으면 JS 프로젝트로 판단
if has_js_services and not has_py_services:
    # → extract_types_js.py 사용
else:
    # → extract_types.py 사용 (Python)
```
