---
description: 웹에디터 설계 원칙 및 작업 가이드 (project)
---

> **공통 지침**: 작업 전 [common.md](common.md) 참조

# 웹에디터 설계 원칙 및 작업 가이드

## 웹에디터 실행
```bash
python mcp_editor/tool_editor_web.py
```

> **자동 스캔**: 웹에디터 시작 시 `@mcp_service` 데코레이터가 있는 함수를 자동 스캔하여 `registry_{server}.json` 업데이트

---

## 1. 목적
MCP 서버의 Tool 인자 및 값을 제어

## 2. 데이터 소스 (서버별 패턴)

| 정보 | 경로 패턴 |
|------|----------|
| 서비스 구현 정보 | `mcp_editor/mcp_service_registry/registry_{server}.json` |
| 도구 정의 (**Single Source of Truth**) | `mcp_editor/mcp_{server}/tool_definition_templates.yaml` |

### 각 파일의 역할

| 파일 | 역할 | 변경 시점 |
|------|------|----------|
| `tool_definition_templates.yaml` | LLM 스키마 + mcp_service_factors (Internal 포함) - **YAML 단일 소스** | 웹에디터에서 저장 시 |
| `registry_{server}.json` | 실제 코드 어디를 호출할지 (implementation) | 소스코드 변경 후 스캔 시 |

> **Note**: `tool_definitions.py`는 더 이상 생성되지 않음. 서버 코드가 런타임에 YAML에서 직접 로드함.

## 3. 네이밍 규칙
→ `docs/terminology.md` 참조

## 4. 생성 대상

### 다중 프로토콜 지원 (v3.0 - YAML Single Source of Truth)
웹에디터에서 "Generate Server" 실행 시 3가지 프로토콜 서버 동시 생성:
- `mcp_{server}/mcp_server/server_rest.py` - REST API 서버 (FastAPI)
- `mcp_{server}/mcp_server/server_stdio.py` - STDIO 프로토콜 서버
- `mcp_{server}/mcp_server/server_stream.py` - Stream 프로토콜 서버 (SSE)

> **삭제됨**: `tool_definitions.py`는 더 이상 생성되지 않음 (v3.0)

### 템플릿 파일
- `jinja/universal_server_template.jinja2` - 통합 서버 템플릿 (모든 프로토콜 지원)

### 수정 원칙
**중요**: 생성 파일 직접 수정 금지. 반드시 아래 파일 수정:
- `jinja/universal_server_template.jinja2` - 서버 템플릿
- `jinja/generate_universal_server.py` - 생성 로직

## 5. 파라미터 분류 원칙

| 분류 | 설명 | LLM 노출 | 저장 위치 |
|------|------|---------|----------|
| **Signature** | LLM이 제공하는 파라미터 | O | `tool_definition_templates.yaml`의 inputSchema |
| **Signature Defaults** | LLM에게 보이지만 기본값 제공 | O | `mcp_service_factors` (source: signature_defaults) |
| **Internal** | 시스템이 고정하는 파라미터 | X | `mcp_service_factors` (source: internal) |

## 6. Generate 흐름

### YAML Single Source of Truth 흐름 (v3.0)
```
tool_definition_templates.yaml  ─┐
(mcp_service_factors 포함)      │
                                 ├─→ generate_universal_server.py ─┬─→ server_rest.py
registry_{server}.json          ─┘                                ├─→ server_stdio.py
                                                                   └─→ server_stream.py

웹에디터 Save 시:
웹에디터 ─→ tool_definition_templates.yaml (YAML 단일 파일만 저장)

런타임 시:
server_*.py ─→ YAML에서 MCP_TOOLS 직접 로드 ─→ SERVICE_FACTORS 추출
```

### 프로토콜별 특징
| 프로토콜 | 용도 | 통신 방식 | 포트 |
|---------|------|----------|------|
| REST | HTTP API 클라이언트용 | HTTP/JSON | 지정 포트 |
| STDIO | CLI/터미널 연동 | 표준 입출력 | N/A |
| Stream | 실시간 이벤트 스트림 | SSE | 지정 포트 |

## 7. 작업 흐름
1. `tool_definition_templates.yaml`에서 도구 정의 확인/수정
2. `registry_{server}.json`에서 서비스 구현 정보 확인
3. 필요시 템플릿 수정
4. `generate_universal_server.py`로 최종 파일 생성

---

## 관련 파일 경로

### 웹에디터 핵심
- `mcp_editor/tool_editor_web.py` - 웹에디터 서버
- `mcp_editor/templates/tool_editor.html` - 웹에디터 UI
- `mcp_editor/editor_config.json` - 에디터 설정

### 서버 생성
- `jinja/generate_universal_server.py` - 다중 프로토콜 서버 생성 스크립트
- `jinja/universal_server_template.jinja2` - 범용 서버 베이스 템플릿
- `jinja/generate_editor_config.py` - editor_config.json 생성
- `jinja/editor_config_template.jinja2` - editor_config 템플릿

### 레지스트리 관리
- `mcp_editor/mcp_service_registry/mcp_service_scanner.py` - 데코레이터 스캔
- `mcp_editor/mcp_service_registry/mcp_service_decorator.py` - @mcp_service
- `mcp_editor/mcp_service_registry/meta_registry.py` - 메타 레지스트리

### 타입 처리
- `mcp_editor/pydantic_to_schema.py` - Pydantic → JSON Schema 변환
- `mcp_editor/extract_graph_types.py` - GraphQL 타입 추출

### 서버 제어
- `mcp_editor/mcp_server_controller.py` - 서버 시작/중지 관리
- `mcp_editor/tool_editor_web_server_mappings.py` - 서버 매핑 정보

---

## 새 MCP 서버 프로젝트 생성

### 사용 방법
1. 웹에디터에서 **"New Project"** 버튼 클릭
2. 서비스 정보 입력 (name, port, description 등)
3. "Create Project" 버튼 클릭

### 생성되는 구조
```
mcp_{service_name}/
├── mcp_server/
│   ├── __init__.py
│   ├── server_rest.py     # REST API 서버
│   ├── server_stdio.py    # STDIO 프로토콜 서버
│   ├── server_stream.py   # Stream 프로토콜 서버
│   └── run.py             # 서버 실행 스크립트
├── {service_name}_service.py  # 비즈니스 로직
├── {service_name}_types.py    # 타입 정의 (선택사항)
└── requirements.txt        # Python 의존성

mcp_editor/mcp_{service_name}/
└── tool_definition_templates.yaml  # 도구 정의 (Single Source of Truth)
```

### 내부 동작
- `jinja/create_mcp_project.py`의 `MCPProjectCreator` 클래스 사용
- 프로젝트 생성 후 `editor_config.json` 자동 업데이트
- 생성 완료 후 3초 뒤 자동 새로고침

---

## MCP 프로토콜 서버 실행

### 프로토콜별 서버 실행 방법
```bash
# REST API 서버 실행 (FastAPI)
python mcp_outlook/mcp_server/server_rest.py
# 또는
cd mcp_outlook/mcp_server && uvicorn server_rest:app --reload --port 8091

# STDIO 프로토콜 서버 실행
python mcp_outlook/mcp_server/server_stdio.py

# Stream 프로토콜 서버 실행 (SSE)
python mcp_outlook/mcp_server/server_stream.py
```

---

## 디버깅 및 테스트

```bash
# 레지스트리 스캔 및 확인
python mcp_editor/mcp_service_registry/mcp_service_scanner.py

# editor_config.json 재생성
python jinja/generate_editor_config.py

# 서버 코드 재생성 (outlook 예시) - 3가지 프로토콜 동시 생성
python jinja/generate_universal_server.py outlook --protocol all

# 특정 프로토콜만 생성
python jinja/generate_universal_server.py outlook --protocol rest
python jinja/generate_universal_server.py outlook --protocol stdio
python jinja/generate_universal_server.py outlook --protocol stream
```

---

## 체크리스트

웹에디터 작업 시:
- [ ] @mcp_service 데코레이터가 모든 서비스 메서드에 있는지 확인
- [ ] registry_{server}.json이 최신 상태인지 확인
- [ ] tool_definition_templates.yaml이 정확한지 확인
- [ ] Internal 파라미터가 올바르게 설정되었는지 확인
- [ ] Generate Server 실행 시 3가지 프로토콜 파일 생성 확인
  - [ ] server_rest.py 생성 및 동작 확인
  - [ ] server_stdio.py 생성 및 동작 확인
  - [ ] server_stream.py 생성 및 동작 확인
- [ ] 서버가 YAML에서 MCP_TOOLS를 정상 로드하는지 확인

---
*Last Updated: 2026-01-08*
*Version: 3.0*
*변경사항: YAML Single Source of Truth 적용, tool_definitions.py 제거, 런타임 YAML 로드*
