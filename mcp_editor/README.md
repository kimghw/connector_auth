# MCP Tool Editor

MCP 서버의 툴 정의를 시각적으로 편집하고 관리하는 웹 기반 에디터입니다.

## 📁 파일 구조 및 용도

### 🌐 웹 에디터 (Core)

#### `tool_editor_web.py`
- **용도**: Flask 기반 웹 에디터 서버 (메인 애플리케이션)
- **기능**:
  - 웹 UI를 통해 MCP 툴 정의 편집
  - `tool_definition_outlook_templates.py`에서 데이터 로드
  - 저장 시 2개 파일 동시 생성:
    - `tool_definition_outlook_templates.py` (메타데이터 포함)
    - `../mcp_outlook/mcp_server/tool_definitions.py` (깨끗한 버전)
  - Pydantic 모델 → JSON Schema 자동 변환
- **실행**: `./run_tool_editor.sh` 또는 `python tool_editor_web.py`

#### `run_tool_editor.sh`
- **용도**: 웹 에디터 실행 스크립트
- **기능**:
  - Flask 서버 시작 (`tool_editor_web.py`)
  - 기본 포트: 8091
  - 브라우저 자동 오픈

#### `templates/tool_editor.html`
- **용도**: 웹 에디터 UI (HTML 템플릿)
- **기능**: 툴 목록, 파라미터 편집, 스키마 미리보기

---

### 📋 툴 정의 파일 (Data)

#### `tool_definition_outlook_templates.py` ⭐
- **용도**: 웹 에디터의 데이터 소스 (메타데이터 포함 버전)
- **내용**:
  ```python
  {
    "name": "mail_search",
    "inputSchema": {...},
    "mcp_service": {  # ← 추가 메타데이터
      "name": "query_search",  # 실제 함수명
      "signature": "user_email: str, search: str, ..."  # 함수 시그니처
    }
  }
  ```
- **특징**:
  - 웹 에디터에서 **로드**할 때 사용 (우선순위 1)
  - 웹 에디터에서 **저장**할 때 자동 업데이트
  - `jinja/generate_outlook_server.py`가 `server.py` 생성 시 참조
  - `mcp_service` 필드로 함수 시그니처 정보 보존

#### `editor_config.json`
- **용도**: 웹 에디터 설정 파일 (다중 프로필 지원)
- **내용**:
  ```json
  {
    "_default": {
      "template_definitions_path": "tool_definition_outlook_templates.py",
      "tool_definitions_path": "../mcp_outlook/mcp_server/tool_definitions.py",
      "graph_types_files": ["../mcp_outlook/outlook_types.py"]
    },
    "outlook": {...},
    "attachment": {...}
  }
  ```
- **생성**: `jinja/generate_editor_config.py`로 자동 생성

---

### 🔧 유틸리티 스크립트

#### `pydantic_to_schema.py`
- **용도**: Pydantic 모델 → JSON Schema 변환기
- **기능**:
  - `graph_types.py` (또는 `outlook_types.py`)의 Pydantic 모델 로드
  - `FilterParams`, `ExcludeParams` 등을 JSON Schema로 변환
  - 웹 에디터에서 "baseModel" 드롭다운 자동 채우기

#### `extract_types.py`
- **용도**: `graph_types.py`에서 Pydantic 모델 추출
- **기능**:
  - AST 파싱으로 모델 클래스 찾기
  - 필드 타입, description, default 값 추출
  - `types_properties.json` 생성

#### `extract_real_mcp_services.py`
- **용도**: 코드베이스에서 `@mcp_service` 데코레이터 스캔
- **기능**:
  - 프로젝트 전체를 재귀 탐색
  - 데코레이터가 붙은 함수 찾기
  - 함수 시그니처, 파라미터 추출
  - `outlook_mcp_services.json`, `outlook_mcp_services_detailed.json` 생성
- **실행**: `python extract_real_mcp_services.py outlook`

#### `mcp_service_extractor.py`
- **용도**: MCP 서비스 함수의 시그니처 추출
- **기능**:
  - `get_signatures_by_name()`: 함수명으로 시그니처 검색
  - 웹 에디터에서 `mcp_service` 필드 자동 채우기에 사용

#### `mcp_service_decorator.py`
- **용도**: `@mcp_service` 데코레이터 정의
- **기능**:
  - 함수를 MCP 툴로 마킹
  - 메타데이터 저장 (tool_name, description, category 등)
  - 레지스트리 패턴으로 툴 관리

#### `tool_editor_web_server_mappings.py`
- **용도**: 서버 이름 매핑 유틸리티
- **기능**:
  - 프로필명 → 서버명 변환
  - 경로 → 서버명 추론
  - `get_server_name_from_profile()`, `get_server_name_from_path()`

#### `generate_schema_from_service.py`
- **용도**: MCP 서비스에서 스키마 자동 생성
- **기능**: (현재 사용 중인지 확인 필요)

---

### 📊 생성된 JSON 파일 (캐시/메타데이터)

#### `outlook_mcp_services.json`
- **생성**: `extract_real_mcp_services.py outlook`
- **내용**: Outlook 서버의 `@mcp_service` 함수 목록 (간단 버전)

#### `outlook_mcp_services_detailed.json`
- **생성**: `extract_real_mcp_services.py outlook`
- **내용**: Outlook 서버의 `@mcp_service` 함수 상세 정보

#### `attachment_mcp_services.json`
- **생성**: `extract_real_mcp_services.py attachment`
- **내용**: Attachment 서버의 `@mcp_service` 함수 목록

#### `attachment_mcp_services_detailed.json`
- **생성**: `extract_real_mcp_services.py attachment`
- **내용**: Attachment 서버의 `@mcp_service` 함수 상세 정보

#### `types_properties.json`
- **생성**: `extract_types.py`
- **내용**: Pydantic 모델의 필드 정보 (캐시)

---

## 🔄 전체 워크플로우

### 1️⃣ 웹 에디터로 툴 정의 편집

```bash
# 웹 에디터 실행
./run_tool_editor.sh

# 브라우저에서 http://localhost:8091 열림
# → tool_definition_outlook_templates.py 로드
# → 툴 편집 (파라미터 추가/수정, 스키마 변경 등)
# → Save 버튼 클릭
# → 2개 파일 동시 저장:
#    [1] tool_definition_outlook_templates.py (메타데이터 포함)
#    [2] ../mcp_outlook/mcp_server/tool_definitions.py (깨끗한 버전)
```

### 2️⃣ server.py 자동 생성

```bash
cd ../jinja
python generate_outlook_server.py --replace

# → tool_definition_outlook_templates.py 로드
# → 템플릿으로 server.py 생성
# → ../mcp_outlook/mcp_server/server.py 업데이트
```

### 3️⃣ 새로운 MCP 서버 추가 시

```bash
# 1. 코드베이스 스캔 (@mcp_service 데코레이터)
cd mcp_editor
python extract_real_mcp_services.py new_server

# 2. editor_config.json 자동 생성
cd ../jinja
python generate_editor_config.py

# 3. 웹 에디터로 툴 정의 작성
cd ../mcp_editor
./run_tool_editor.sh
```

---

## 📌 주요 데이터 흐름

### 데이터 로드 (웹 에디터 오픈 시)

```
tool_definition_outlook_templates.py  ← [우선순위 1]
  ↓
웹 에디터 UI
  ↓
브라우저에서 편집
```

### 데이터 저장 (Save 버튼 클릭 시)

```
웹 에디터 UI
  ↓
2개 파일 동시 저장:
  ├─ [A] tool_definition_outlook_templates.py (메타데이터 포함)
  │      └─ mcp_service.name, mcp_service.signature 유지
  │
  └─ [B] ../mcp_outlook/mcp_server/tool_definitions.py (깨끗한 버전)
         └─ MCP 프로토콜용, Claude/OpenAI API 전송용
```

### server.py 생성

```
jinja/generate_outlook_server.py
  ↓
tool_definition_outlook_templates.py 로드
  ↓
mcp_service 메타데이터로 함수 시그니처 파악
  ↓
outlook_server_template.jinja2
  ↓
../mcp_outlook/mcp_server/server.py 생성 ✅
```

---

## 🎯 핵심 개념

### 2가지 툴 정의 파일의 차이

| 파일 | 위치 | 메타데이터 | 용도 |
|------|------|-----------|------|
| `tool_definition_outlook_templates.py` | `mcp_editor/` | ✅ 포함 (`mcp_service`) | 웹 에디터 데이터 소스, server.py 생성 입력 |
| `tool_definitions.py` | `mcp_outlook/mcp_server/` | ❌ 제거됨 | 실제 MCP 서버에서 사용, API 전송용 |

### 메타데이터 필드

```python
"mcp_service": {
    "name": "query_search",  # 실제 함수명 (서버 생성 시 사용)
    "signature": "user_email: str, search: str, ..."  # 파라미터 타입
}
```

---

## 🚀 빠른 시작

```bash
# 1. 웹 에디터 실행
./run_tool_editor.sh

# 2. 브라우저에서 툴 편집
# http://localhost:8091

# 3. server.py 재생성 (필요 시)
cd ../jinja
python generate_outlook_server.py --replace
```

---

## 📝 참고사항

- `tool_definition_outlook_templates.py`는 **자동 생성 파일**이지만 **편집 가능**합니다
- 웹 에디터로 저장하면 자동으로 업데이트됩니다
- `mcp_service` 메타데이터를 수동으로 추가하면 server.py 생성 시 반영됩니다
- `editor_config.json`으로 여러 MCP 서버를 동시에 관리할 수 있습니다
