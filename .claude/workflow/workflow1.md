# MCP 웹 에디터 워크플로우 요약

## 전체 흐름

```
서비스 정의 → 설정 생성 → registry/types JSON 생성 → 웹 에디터 UI
```

## 빠른 시작 (Quick Start)

```bash
# 1. 설정 파일 생성
cd /home/kimghw/Connector_auth/mcp_editor/test
./generate_config.sh

# 2. 웹 에디터 시작
cd /home/kimghw/Connector_auth/mcp_editor/tool_editor_core
python -c "from app import run_app; run_app()"

# 3. 브라우저에서 접속
# http://localhost:{port} (포트는 콘솔 출력 확인)
```

---

## 새 프로젝트 설정 순서

### Step 1. 서비스에 데코레이터/JSDoc 추가 (핵심!)

**Python:**
```python
@mcp_service(
    tool_name="handler_xxx",
    server_name="새서버명",      # ← 이것만 지정하면 나머지 자동
    service_name="xxx_service",
    description="설명"
)
def my_service(...):
    ...
```

**JavaScript (JSDoc 방식 - 권장):**
```javascript
/**
 * @mcp_service
 * @server_name 새서버명
 * @tool_name handler_xxx
 * @service_name xxxService
 * @description 설명
 * @param {string} name - 이름
 * @param {number} [age] - 나이 (선택)
 * @returns {Object} 결과
 */
async function myService(name, age) { ... }
```

### Step 2. 설정 파일 생성

**방법 1: 쉘 스크립트 사용 (권장)**
```bash
cd mcp_editor/test
./generate_config.sh           # editor_config.json 생성
./generate_config.sh --dry-run # 발견된 서버만 표시 (생성 안함)
./generate_config.sh --clean   # 기존 config 삭제 후 새로 생성
./generate_config.sh --show    # 현재 editor_config.json 내용 표시
```

**방법 2: Python 스크립트 직접 실행**
```bash
cd mcp_editor
python -m service_registry.config_generator
```

자동으로 생성 (mcp_editor/ 내부):
- `mcp_{server}/registry_{server}.json` - 서비스 메타데이터
- `mcp_{server}/types_property_{server}.json` - 타입 정의
- `editor_config.json` - 프로필 설정

### Step 3. 웹 에디터 시작

```bash
cd mcp_editor/tool_editor_core
python -c "from app import run_app; run_app()"
```

### Step 4. 웹 에디터에서 도구 편집

```
브라우저 → http://localhost:{port}
→ 프로필 선택 (새서버명)
→ 서비스 목록 확인
→ 도구 정의 편집/저장
```

### 요약 테이블

| 순서 | 작업 | 수동/자동 |
|------|------|----------|
| 1 | **`@mcp_service` 데코레이터/JSDoc 추가** | 수동 |
| 2 | 설정 생성 (`generate_config.sh` 또는 직접 실행) | 반자동 |
| 3 | 웹 에디터 시작 | 수동 |
| 4 | UI에서 도구 편집 | 수동 |

> **핵심**: `server_name`만 지정하면 나머지는 자동!

---

## 지원 언어

| 언어 | 확장자 | 서비스 정의 방식 | 타입 정의 | 파서 |
|------|--------|-----------------|----------|------|
| **Python** | `.py` | `@mcp_service` 데코레이터 | BaseModel/dataclass | `ast` (내장) |
| **JavaScript** | `.js`, `.mjs` | `@mcp_service` JSDoc 주석 | Sequelize 모델 | regex (내장) |
| **TypeScript** | `.ts`, `.tsx` | `@McpService` 데코레이터 | - | `esprima` (선택) |

> **참고**: JavaScript는 JSDoc 주석 방식 권장 (esprima 불필요)

---

## 1. 서비스 정의 패턴

### Python - 데코레이터 방식 (decorator.md)

```python
@mcp_service(
    tool_name="handler_mail_list",
    server_name="outlook",        # ← 핵심 필드
    service_name="query_mail_list",
    description="메일 리스트 조회",
    category="outlook_mail",      # 권장
    tags=["query", "search"]      # 권장
)
def query_mail_list(self, ...):
    ...
```

### JavaScript - JSDoc 방식 (권장)

```javascript
/**
 * @mcp_service
 * @server_name asset_management
 * @tool_name search_ships
 * @service_name searchShips
 * @description 선박을 검색합니다
 * @category ship_query
 * @tags query,search,filter
 * @param {string} [name] - 선박 이름
 * @param {string} [imo] - IMO 번호
 * @param {mstShip} shipData - 선박 정보 객체
 * @param {string} shipData.shipName - 선박명 (중첩 속성)
 * @returns {Array<mstShip>} 선박 목록
 */
async function searchShips(name, imo, shipData) { ... }
```

> **JSDoc 규칙**:
> - `@mcp_service` 태그 필수 (스캔 대상 표시)
> - `[param]` 대괄호는 optional 파라미터
> - `@tags`는 쉼표로 구분 (배열로 파싱)
> - **중첩 속성**: `@param {type} parent.child - 설명` 형식 지원

**흐름**:
```
Python:     @mcp_service 데코레이터 → AST 스캔 → registry/types JSON
JavaScript: @mcp_service JSDoc 주석 → 정규식 스캔 → registry/types JSON
```

---

## 2. editor_config.json (editor_config.md)

**위치**: `mcp_editor/editor_config.json`

**역할**: 프로필별 경로/포트 설정

**자동 생성**: 웹 에디터 시작 시 `service_registry.config_generator` 자동 실행

**흐름**:
```
Python:     @mcp_service(server_name="outlook")    → 스캔 → editor_config.json
JavaScript: @mcp_service + @server_name xxx        → 스캔 → editor_config.json
```

**구조 예시**:
```json
{
  "outlook": {
    "template_definitions_path": "mcp_outlook/tool_definition_templates.py",
    "tool_definitions_path": "../mcp_outlook/mcp_server/tool_definitions.py",
    "backup_dir": "mcp_outlook/backups",
    "types_files": ["../mcp_outlook/outlook_types.py"],
    "language": "python",
    "host": "0.0.0.0",
    "port": 8004
  },
  "asset_management": {
    "template_definitions_path": "mcp_asset_management/tool_definition_templates.py",
    "tool_definitions_path": "../mcp_asset_management/mcp_server/tool_definitions.py",
    "backup_dir": "mcp_asset_management/backups",
    "types_files": [
      "../mcp_asset_management/asset-api/sequelize/models2/mst_employee.js",
      "../mcp_asset_management/asset-api/sequelize/models2/employee_license.js"
    ],
    "language": "javascript",
    "host": "0.0.0.0",
    "port": 8001
  }
}
```

**자동 설정 항목** (수동 편집 불필요):
- `template_definitions_path` → `mcp_{server}/tool_definition_templates.py`
- `tool_definitions_path` → `../mcp_{server}/mcp_server/tool_definitions.py`
- `backup_dir` → `mcp_{server}/backups`
- `types_files` → Python: import 추적, JavaScript: Sequelize 모델 디렉토리 탐지
- `language` → 자동 탐지 (`python` 또는 `javascript`)
- `port` → 8001부터 순차 할당

---

## 3. 타입 추출 (extract_types.md)

**역할**: 서비스 파라미터의 커스텀 클래스/모델 프로퍼티 자동 추출

**출력 경로**: `mcp_editor/mcp_{server}/types_property_{server}.json`

### Python
```
서비스 파라미터 (type:"object", class_name:"FilterParams")
         ↓
import 추적 (resolve_class_file)
         ↓
BaseModel 클래스 프로퍼티 추출 (service_registry.python.types)
```

### JavaScript
```
models 디렉토리 자동 탐지 (model/sequelize 키워드)
         ↓
sequelize.define() 파싱 (service_registry.javascript.types)
         ↓
DataTypes 필드 추출 → JSON Schema 타입 변환
```

**특징**:
- Python: import 경로 자동 추적 (상대/절대 import 모두 지원)
- JavaScript: models 디렉토리 자동 스캔 (model/sequelize 키워드 포함 경로)

**웹 에디터에서 사용**:
- API: `GET /api/graph-types-properties`
- UI: 타입 프로퍼티 드롭다운에서 선택 가능

---

## 4. 레지스트리 서버 (registry_server.md)

**역할**: 서비스 메타데이터 저장소

**생성**: `service_registry.scanner:export_services_to_json()` 호출

**출력 경로**: `mcp_editor/mcp_{server}/registry_{server}.json`

**구조**:
```json
{
  "version": "1.0",
  "generated_at": "2026-01-14T...",
  "server_name": "outlook",
  "language": "python",
  "services": {
    "query_mail_list": {
      "service_name": "query_mail_list",
      "handler": {
        "class_name": "MailService",
        "instance": "mail_service",
        "method": "query_mail_list",
        "is_async": true,
        "file": "/path/to/service.py",
        "line": 64
      },
      "signature": "user_email: str, filter_params: Optional[FilterParams]",
      "parameters": [
        { "name": "user_email", "type": "str", "is_optional": false },
        { "name": "filter_params", "type": "object", "class_name": "FilterParams", "is_optional": true }
      ],
      "metadata": { "tool_name": "handler_mail_list", "description": "...", "category": "...", "tags": [...] },
      "pattern": null
    }
  }
}
```

**API 엔드포인트**:
- `GET /api/mcp-services` - 서비스 목록 (드롭다운용)
- `GET /api/registry` - 레지스트리 파일 전체 반환

---

## 통합 데이터 흐름

### Python 프로젝트

```
[소스 코드]
@mcp_service(server_name="outlook") 데코레이터
        │
        ▼
[설정 생성] (택 1)
├── mcp_editor/test/generate_config.sh (권장)
└── python -m service_registry.config_generator
        │
        ├─→ AST 파싱으로 server_name 추출
        ├─→ import 추적으로 types_files 자동 탐지
        └─→ editor_config.json 생성/갱신
        │
        ▼
[웹 에디터 시작]
mcp_editor/tool_editor_core/app.py:run_app()
        │
        └─→ tool_editor_core/service_registry.py:scan_all_registries()
                  │
                  └─→ service_registry.scanner:export_services_to_json()
                            │
                            ├─→ python.scanner:find_mcp_services_in_python_file() (AST 스캔)
                            ├─→ collect_referenced_types() → python.types
                            │
                            ├─→ mcp_outlook/registry_outlook.json 생성
                            └─→ mcp_outlook/types_property_outlook.json 생성
                                      │
                                      ▼
[웹 에디터 UI]
프로필 선택 → 서비스 목록 → 도구 편집
```

### JavaScript 프로젝트

```
[소스 코드]
/** @mcp_service @server_name asset_management ... */
async function searchShips(...) { }

sequelize.define('mstShip', { fields })
        │
        ▼
[설정 생성] (택 1)
├── mcp_editor/test/generate_config.sh (권장)
└── python -m service_registry.config_generator
        │
        ├─→ JSDoc 정규식으로 @server_name 추출
        ├─→ Sequelize 모델 디렉토리 자동 탐지
        └─→ editor_config.json 생성/갱신
        │
        ▼
[웹 에디터 시작]
mcp_editor/tool_editor_core/app.py:run_app()
        │
        └─→ tool_editor_core/service_registry.py:scan_all_registries()
                  │
                  └─→ service_registry.scanner:export_services_to_json()
                            │
                            ├─→ javascript.scanner:find_jsdoc_mcp_services_in_js_file() (정규식 스캔)
                            ├─→ javascript.types (Sequelize 모델 추출)
                            │
                            ├─→ mcp_asset_management/registry_asset_management.json 생성
                            └─→ mcp_asset_management/types_property_asset_management.json 생성
                                      │
                                      ▼
[웹 에디터 UI]
프로필 선택 → 서비스 목록 → 도구 편집
```

---

## 핵심 포인트

1. **언어 자동 감지**: Python/JavaScript 프로젝트 자동 판별 (확장자 기반)
2. **설정 파일 수동 편집 불필요**: 스캔 기반 자동 생성
3. **타입 추적 자동화**:
   - Python: import 경로 따라 BaseModel 추출 (`python.types`)
   - JavaScript: models 디렉토리에서 Sequelize 모델 추출 (`javascript.types`)
4. **핵심 필드 `server_name`**:
   - 프로필 키: `editor_config.json`의 프로필 이름
   - 경로 컨벤션: `mcp_{server_name}/` 폴더 자동 생성
   - 파일 이름: `registry_{server_name}.json`, `types_property_{server_name}.json`
   - 포트: 8001부터 순차 할당
5. **설정 생성 권장 방법**: `mcp_editor/test/generate_config.sh` 쉘 스크립트 사용

---

## 출력 파일 경로

| 파일 | 경로 (mcp_editor/ 기준) |
|------|------------------------|
| **editor_config.json** | `mcp_editor/editor_config.json` |
| **registry** | `mcp_editor/mcp_{server}/registry_{server}.json` |
| **types_property** | `mcp_editor/mcp_{server}/types_property_{server}.json` |
| **tool_definition_templates** | `mcp_editor/mcp_{server}/tool_definition_templates.py` |
| **backups** | `mcp_editor/mcp_{server}/backups/` |

> **변경됨**: 기존 `mcp_service_registry/` 경로에서 `mcp_{server}/` 경로로 통일

---

## service_registry 폴더 구조

```
service_registry/
├── __init__.py          # 루트 패키지 (하위 호환성 export)
├── base.py              # 공통 유틸리티 (Language enum, detect_language 등)
├── scanner.py           # 통합 스캐너 (모든 언어 지원, 하위 모듈 re-export)
├── config_generator.py  # editor_config.json 생성기
├── meta_registry.py     # 메타 레지스트리
├── python/
│   ├── __init__.py      # Python 모듈 export
│   ├── scanner.py       # Python AST 스캐너
│   ├── types.py         # Python 타입 추출 (Pydantic BaseModel)
│   └── decorator.py     # @mcp_service 데코레이터
└── javascript/
    ├── __init__.py      # JavaScript 모듈 export
    ├── scanner.py       # JavaScript/JSDoc 스캐너
    └── types.py         # Sequelize 타입 추출
```

### 파일명 변경 매핑 (기존 → 신규)

| 기존 파일명 | 신규 위치 |
|------------|----------|
| `mcp_service_scanner.py` | `scanner.py` |
| `generate_editor_config.py` | `config_generator.py` |
| `scanner_base.py` | `base.py` |
| `scanner_python.py` | `python/scanner.py` |
| `scanner_javascript.py` | `javascript/scanner.py` |
| `extract_types.py` | `python/types.py` |
| `extract_types_js.py` | `javascript/types.py` |
| `mcp_service_decorator.py` | `python/decorator.py` |

### 하위 호환성

기존 import 경로를 유지하기 위해 `__init__.py`에서 주요 함수/클래스를 re-export합니다:

```python
# 기존 사용법 유지
from service_registry import scan_codebase_for_mcp_services
from service_registry import extract_types, extract_types_js
from service_registry import mcp_service, MCP_SERVICE_REGISTRY
```

---

## 관련 스크립트

| 스크립트 | 경로 | 역할 |
|----------|------|------|
| `scanner.py` | `mcp_editor/service_registry/` | 서비스 스캔 + 파라미터 추출 (Python/JS 통합) |
| `python/scanner.py` | `mcp_editor/service_registry/python/` | Python AST 기반 스캔 |
| `python/types.py` | `mcp_editor/service_registry/python/` | Python BaseModel 타입 추출 |
| `python/decorator.py` | `mcp_editor/service_registry/python/` | @mcp_service 데코레이터 정의 |
| `javascript/scanner.py` | `mcp_editor/service_registry/javascript/` | JavaScript JSDoc 정규식 스캔 |
| `javascript/types.py` | `mcp_editor/service_registry/javascript/` | JavaScript Sequelize 모델 추출 |
| `config_generator.py` | `mcp_editor/service_registry/` | editor_config.json 자동 생성 |
| `base.py` | `mcp_editor/service_registry/` | 공통 유틸리티 (Language enum 등) |
| `generate_config.sh` | `mcp_editor/test/` | editor_config.json 생성 쉘 스크립트 (권장) |
| `app.py` | `mcp_editor/tool_editor_core/` | 웹 에디터 시작점 |
| `service_registry.py` | `mcp_editor/tool_editor_core/` | 레지스트리 스캔 관리 |

### generate_config.sh 옵션

| 옵션 | 설명 |
|------|------|
| (없음) | editor_config.json 생성 |
| `--dry-run`, `-n` | 발견된 서버만 표시 (파일 생성 안함) |
| `--clean`, `-c` | 기존 config 삭제 후 새로 생성 |
| `--show`, `-s` | 현재 editor_config.json 내용 표시 |
| `--help`, `-h` | 도움말 표시 |

---

## 주요 함수 참조

### service_registry.scanner (통합 스캐너)

| 함수 | 용도 |
|------|------|
| `scan_codebase_for_mcp_services()` | 코드베이스 전체 스캔 (Python + JS) |
| `export_services_to_json()` | registry + types_property JSON 생성 |
| `get_services_map()` | 서비스 메타데이터 맵 반환 |

### service_registry.python.scanner

| 함수 | 용도 |
|------|------|
| `find_mcp_services_in_python_file()` | Python AST 기반 데코레이터 스캔 |
| `extract_decorator_metadata()` | 데코레이터 메타데이터 추출 |
| `MCPServiceExtractor` | AST NodeVisitor 클래스 |
| `signature_from_parameters()` | 파라미터에서 시그니처 문자열 생성 |

### service_registry.javascript.scanner

| 함수 | 용도 |
|------|------|
| `find_jsdoc_mcp_services_in_js_file()` | JavaScript JSDoc 정규식 스캔 |
| `find_mcp_services_in_js_file()` | esprima 기반 스캔 (선택) |

### service_registry.python.types

| 함수 | 용도 |
|------|------|
| `extract_class_properties()` | BaseModel 클래스 프로퍼티 추출 |
| `extract_single_class()` | 단일 클래스 프로퍼티 추출 |

### service_registry.javascript.types

| 함수 | 용도 |
|------|------|
| `scan_js_project_types()` | Sequelize 모델 디렉토리 스캔 |
| `export_js_types_property()` | types_property JSON 생성 |
| `extract_sequelize_models_from_file()` | 단일 파일에서 모델 추출 |

### service_registry.config_generator

| 함수 | 용도 |
|------|------|
| `scan_codebase_for_servers()` | Python/JS 통합 서버명 스캔 |
| `extract_server_name_from_py_file()` | Python AST로 server_name 추출 |
| `extract_server_name_from_js_file()` | JavaScript JSDoc로 @server_name 추출 |
| `generate_editor_config_json()` | editor_config.json 생성 |

### tool_editor_core/service_registry.py

| 함수 | 용도 |
|------|------|
| `scan_all_registries()` | 웹 에디터 시작 시 전체 프로필 스캔 |
| `load_services_for_server()` | 저장 시 서비스 메타데이터 로드 |
