# 기존 서비스 재사용 MCP 프로젝트 생성 및 삭제 기능 구현 계획

> **공통 지침**: 작업 전 [common.md](../commands/common.md) 참조
> **네이밍 규칙**: [terminology.md](../commands/terminology.md) 준수

## 문서 정보

- **작성일**: 2026-01-10
- **버전**: 4.0 (선행 수정 사항 추가)
- **상태**: 선행 작업 필요, 구현 대기
- **기능**:
  1. 기존 MCP 서비스 재사용하여 새 프로필 생성
  2. MCP 프로필 삭제

---

## 0. 선행 수정 사항 (필수)

> ⚠️ **중요**: 아래 이슈들을 먼저 해결하지 않으면 "프로필별 툴셋 분리"가 정상 동작하지 않습니다.

### 0.1 치명적 이슈 (🔴 필수)

#### 0.1.1 YAML 경로 하드코딩

**파일**: [universal_server_template.jinja2:103](../../jinja/universal_server_template.jinja2#L103)

**현재 코드**:
```python
yaml_path = Path(current_dir).parent.parent / "mcp_editor" / "mcp_{{ server_name }}" / "tool_definition_templates.yaml"
```

**문제**: `server_name`이 템플릿 렌더링 시점에 고정됨. `outlook_read` 프로필로 생성해도 런타임에 잘못된 경로를 참조할 수 있음.

**수정안**:
```python
# 옵션 A: 서버 디렉토리 기준 상대 경로 (권장)
yaml_path = Path(current_dir) / "tool_definition_templates.yaml"

# 옵션 B: 환경변수로 주입
yaml_path = Path(os.environ.get("MCP_YAML_PATH", default_path))
```

**상태**: 🔴 구현 필요

---

#### 0.1.2 서버 경로 추론 로직

**파일**: [mcp_server_controller.py:38-39](../../mcp_editor/mcp_server_controller.py#L38-L39)

**현재 코드**:
```python
if "outlook" in self.profile.lower():
    base_path = os.path.join(ROOT_DIR, "mcp_outlook", "mcp_server")
```

**문제**: `outlook_read` 프로필은 `"outlook" in profile`이 `True`라서 항상 `mcp_outlook/mcp_server`를 실행. `mcp_outlook_read/mcp_server`를 실행하지 않음.

**수정안**:
```python
def _get_server_path(self) -> Optional[str]:
    """editor_config.json에서 서버 경로를 직접 읽기"""
    config = load_editor_config()
    if self.profile in config:
        tool_def_path = config[self.profile].get("tool_definitions_path", "")
        if tool_def_path:
            # tool_definitions_path에서 mcp_server 디렉토리 추출
            return os.path.dirname(os.path.join(ROOT_DIR, "mcp_editor", tool_def_path))
    return None
```

**상태**: 🔴 구현 필요

---

### 0.2 중요 이슈 (🟡 권장)

#### 0.2.1 포트 고정

**파일**: [universal_server_template.jinja2:728](../../jinja/universal_server_template.jinja2#L728)

**현재 코드**:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

**문제**: 모든 REST 서버가 포트 8000 사용 → 다중 프로필 실행 시 충돌

**수정안**:
```python
# Jinja2 변수로 포트 주입
uvicorn.run(app, host="0.0.0.0", port={{ port | default(8000) }})

# 또는 환경변수/CLI 인자로 받기
port = int(os.environ.get("MCP_SERVER_PORT", 8000))
uvicorn.run(app, host="0.0.0.0", port=port)
```

**상태**: 🟡 구현 필요

---

#### 0.2.2 `createNewProject()` 함수 중복

**파일**: [tool_editor_tools.js](../../mcp_editor/static/js/tool_editor_tools.js)

**현재 상태**:
- Line 528: `function createNewProject()` (동기)
- Line 758: `async function createNewProject()` (비동기)

**문제**: 후자가 전자를 덮어씀. 어떤 버전이 실행될지 예측 불가.

**수정안**: 중복 제거 후 하나로 통합 (Line 528 버전 삭제)

**상태**: 🟡 구현 필요

---

#### 0.2.3 `discover_mcp_modules()` 경로 우선순위

**파일**: [tool_editor_web.py:337](../../mcp_editor/tool_editor_web.py#L337)

**현재 코드**:
```python
editor_template_defs = os.path.join(ROOT_DIR, "mcp_editor", f"mcp_{server_name}", "tool_definition_templates.py")
```

**문제**: `server_name`이 원본 서비스명(`outlook`)으로 추출되면, `mcp_outlook_read` 모듈 선택 시에도 `mcp_editor/mcp_outlook/` 경로를 우선 사용

**수정안**:
```python
# 프로필명 기반으로 경로 결정
# 또는 editor_config.json의 template_definitions_path 참조
profile_name = entry.replace("mcp_", "")  # mcp_outlook_read → outlook_read
editor_template_defs = os.path.join(ROOT_DIR, "mcp_editor", f"mcp_{profile_name}", "tool_definition_templates.py")
```

**상태**: 🟡 구현 필요

---

#### 0.2.4 `editor_config.json` 재생성 문제

**파일**:
- [create_mcp_project.py:832](../../jinja/create_mcp_project.py#L832) → `_run_generate_editor_config()` 호출
- [generate_editor_config.py:212](../../jinja/generate_editor_config.py#L212)

**현재 동작**:
```python
# generate_editor_config.py가 @mcp_service 데코레이터를 스캔해서 config를 새로 생성
config_output_path = os.path.join(project_root, "mcp_editor", "editor_config.json")
```

**문제**: 수동 추가한 재사용 프로필이 덮어써짐

**수정안**: Merge 전략 적용
```python
def generate_editor_config(...):
    existing_config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            existing_config = json.load(f)

    generated_config = generate_from_decorators()

    # 기존 프로필 중 generated에 없는 것은 보존 (재사용 프로필)
    for profile, conf in existing_config.items():
        if profile not in generated_config:
            # "is_reused" 플래그가 있거나 generated에 없으면 보존
            if conf.get("is_reused") or profile not in generated_config:
                generated_config[profile] = conf

    # 저장
    with open(config_path, 'w') as f:
        json.dump(generated_config, f, indent=2)
```

**상태**: 🟡 구현 필요

---

### 0.3 구현 순서

| 순서 | 작업 | 파일 | 우선순위 |
|-----|------|------|---------|
| 0-1 | `createNewProject()` 중복 제거 | tool_editor_tools.js | 🔴 선행 필수 |
| 0-2 | 서버 경로 추론 로직 수정 | mcp_server_controller.py | 🔴 필수 |
| 0-3 | YAML 경로 수정 | universal_server_template.jinja2 | 🔴 필수 |
| 0-4 | 포트 변수화 | universal_server_template.jinja2 | 🟡 중요 |
| 0-5 | editor_config.json merge 전략 | generate_editor_config.py | 🟡 중요 |
| 0-6 | discover_mcp_modules() 경로 수정 | tool_editor_web.py | 🟡 중요 |
| 1~4 | 본 기능 구현 (섹션 5 참조) | 여러 파일 | 🟢 본 작업 |

---

## 1. 기능 개요

### 1.1 서비스 재사용 생성

**목적**: 같은 서비스 로직을 사용하되 노출하는 도구만 다른 프로필 생성

**핵심 방식**: YAML 템플릿 복사 + editor_config.json 프로필 추가
- **YAML 템플릿 복사**: `mcp_editor/mcp_{existing}/tool_definition_templates.yaml` 전체 복사
- **editor_config.json 업데이트**: 같은 source_dir 참조, 새 프로필 추가
- **선택적 편집**: 웹에디터에서 불필요한 도구 삭제

**예시**:
```
기존: outlook (11개 도구, mcp_outlook 폴더 참조)
    ↓ 재사용
신규: outlook_read (YAML 복사 → 웹에디터에서 6개만 선택) - 읽기 전용
    ↓ 재사용
신규: outlook_process (YAML 복사 → 웹에디터에서 5개만 선택) - 쓰기 권한
```

**장점**:
- ✅ 코드 중복 없음 (같은 mcp_outlook/outlook_service.py 사용)
- ✅ 권한 분리 (도구별 서버 분리)
- ✅ 중앙 Registry 관리 (mcp_editor/mcp_service_registry/)
- ✅ 메타데이터 보존 (inputSchema, mcp_service_factors)

### 1.2 프로필 삭제

**목적**: 생성된 MCP 프로필 완전 삭제

**삭제 대상**:
- `mcp_editor/mcp_{profile_name}/` 폴더
- `mcp_{profile_name}/` 폴더 (선택적 - 서버 프로젝트가 있는 경우)
- `editor_config.json`에서 프로필 제거

---

## 2. 실제 프로젝트 구조 분석

### 2.1 현재 디렉토리 구조

```
/home/kimghw/Connector_auth/
├── mcp_outlook/                          # 원본 서비스 소스 ✅
│   ├── outlook_service.py                # MailService 클래스
│   ├── outlook_types.py                  # FilterParams, SelectParams 등
│   └── mcp_server/                       # 생성된 서버 (Generate Server로 생성)
│       ├── server_rest.py
│       ├── server_stdio.py
│       └── server_stream.py
│
├── mcp_calendar/                         # 원본 서비스 소스
│   ├── calendar_service.py
│   ├── calendar_types.py
│   └── mcp_server/
│
├── mcp_file_handler/                     # 원본 서비스 소스
│   ├── file_manager.py
│   └── mcp_server/
│
├── mcp_editor/                           # 웹에디터 및 설정 중앙 관리 ✅
│   ├── editor_config.json                # 프로필 설정 (outlook, calendar, file_handler)
│   ├── tool_editor_web.py                # 웹에디터 API 서버
│   │
│   ├── mcp_service_registry/             # Registry 중앙 저장소 ✅
│   │   ├── registry_outlook.json         # outlook 서비스 메타데이터
│   │   ├── registry_calendar.json
│   │   ├── registry_file_handler.json
│   │   ├── mcp_service_scanner.py
│   │   └── meta_registry.py
│   │
│   ├── mcp_outlook/                      # outlook 프로필 YAML ✅
│   │   ├── tool_definition_templates.yaml
│   │   ├── tool_definition_templates.py
│   │   └── backups/
│   │
│   ├── mcp_calendar/                     # calendar 프로필 YAML
│   │   ├── tool_definition_templates.yaml
│   │   └── ...
│   │
│   └── mcp_file_handler/                 # file_handler 프로필 YAML
│       └── ...
│
└── jinja/                                # 서버 생성 도구
    ├── create_mcp_project.py             # MCPProjectCreator
    ├── generate_universal_server.py
    └── universal_server_template.jinja2
```

### 2.2 editor_config.json 구조

```json
{
  "outlook": {
    "source_dir": "../mcp_outlook",
    "template_definitions_path": "mcp_outlook/tool_definition_templates.py",
    "tool_definitions_path": "../mcp_outlook/mcp_server/tool_definitions.py",
    "backup_dir": "mcp_outlook/backups",
    "types_files": ["../mcp_outlook/outlook_types.py"],
    "host": "0.0.0.0",
    "port": 8091
  },
  "calendar": {
    "source_dir": "../mcp_calendar",
    "template_definitions_path": "mcp_calendar/tool_definition_templates.py",
    ...
  }
}
```

### 2.3 Registry 파일 구조 (중앙 관리)

**파일 위치**: `mcp_editor/mcp_service_registry/registry_outlook.json`

```json
{
  "version": "1.0",
  "generated_at": "2026-01-10T09:46:37.666365",
  "server_name": "outlook",
  "services": {
    "query_mail_list": {
      "service_name": "query_mail_list",
      "handler": {
        "class_name": "MailService",
        "module_path": "outlook.outlook_service",
        "instance": "mail_service",
        "method": "query_mail_list",
        "is_async": true
      },
      "signature": "user_email: str, query_method: Optional[QueryMethod] = ...",
      "parameters": [ ... ],
      "metadata": {
        "description": "메일 리스트 조회 기능",
        "category": "outlook_mail",
        "tags": ["query", "search"]
      }
    }
  }
}
```

---

## 3. 서비스 재사용 생성 플로우

```
┌─────────────────────────────────────────────────────┐
│ 1. UI 추가 (Create New MCP Project 모달)            │
│    - 프로젝트 타입 선택: "new" / "reuse"            │
│    - reuse 선택 시 기존 서비스 드롭다운 표시         │
│    - 새 프로필 이름 입력 (suffix)                    │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ 2. API 엔드포인트 수정                               │
│    POST /api/create-mcp-project                     │
│    - project_type: "new" | "reuse"                  │
│    - existing_service: "outlook" (reuse인 경우)     │
│    - new_profile_name: "outlook_read"               │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ 3. YAML 템플릿 복사 ✅ 핵심                          │
│    copy_yaml_templates()                            │
│    - mcp_editor/mcp_{existing}/*.yaml 복사          │
│    - mcp_editor/mcp_{new_profile}/ 생성             │
│    - tool_definition_templates.py도 복사            │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ 4. editor_config.json 업데이트                      │
│    update_editor_config_for_reuse()                 │
│    - 기존 프로필의 source_dir 재사용                │
│    - template_definitions_path: mcp_{new_profile}/  │
│    - 새 프로필 추가                                  │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ 5. 서버 프로젝트 폴더 생성 (선택적)                  │
│    create_server_project_folder()                   │
│    - mcp_{new_profile}/ 폴더 생성                   │
│    - mcp_{new_profile}/mcp_server/ 폴더 생성        │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ 6. 웹에디터에서 도구 편집                            │
│    - 프로필 선택: outlook_read                      │
│    - 불필요한 도구 삭제 (11개 → 6개)                │
│    - Generate Server 클릭                           │
└─────────────────────────────────────────────────────┘
```

---

## 4. 프로필 삭제 플로우

```
┌─────────────────────────────────────────────────────┐
│ 1. UI 추가 (프로필 목록에 삭제 버튼)                 │
│    - 각 프로필 탭에 X 버튼 추가                      │
│    - 원본 프로필 (outlook, calendar) 삭제 방지       │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ 2. API 엔드포인트 추가                               │
│    DELETE /api/delete-mcp-profile                   │
│    - profile_name 파라미터                          │
│    - 원본 프로필 삭제 방지 로직                      │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ 3. 삭제 함수                                         │
│    delete_mcp_profile()                             │
│    - mcp_editor/mcp_{profile}/ 폴더 삭제            │
│    - mcp_{profile}/ 폴더 삭제 (있는 경우)           │
│    - editor_config.json 프로필 제거                 │
└─────────────────────────────────────────────────────┘
```

---

## 5. 상세 구현 사양

### 5.1 Task 1: API 엔드포인트 수정

**파일**: `/home/kimghw/Connector_auth/mcp_editor/tool_editor_web.py`

#### 5.1.1 프로필 생성 API 수정 (라인 1963-2013)

```python
@app.route("/api/create-mcp-project", methods=["POST"])
def create_new_mcp_project():
    """Create a new MCP project or reuse existing service"""
    try:
        data = request.json or {}

        # 공통 파라미터
        project_type = data.get("project_type", "new")  # "new" | "reuse"
        port = data.get("port", 8080)

        if project_type == "new":
            # 기존 로직 (MCPProjectCreator 사용)
            service_name = data.get("service_name", "").lower()
            description = data.get("description", "")
            author = data.get("author", "")
            include_types = data.get("include_types", True)

            if not service_name:
                return jsonify({"error": "service_name is required"}), 400

            # ... 기존 MCPProjectCreator 로직 유지 ...

        elif project_type == "reuse":
            # 새 로직 (서비스 재사용)
            existing_service = data.get("existing_service", "").lower()
            new_profile_name = data.get("new_profile_name", "").lower()

            if not existing_service or not new_profile_name:
                return jsonify({"error": "existing_service and new_profile_name are required"}), 400

            # 프로필 이름 검증
            if not new_profile_name.replace("_", "").isalnum():
                return jsonify({"error": "Profile name should only contain letters, numbers, and underscores"}), 400

            # 프로필 중복 확인
            if new_profile_name in list_profile_names():
                return jsonify({"error": f"Profile '{new_profile_name}' already exists"}), 400

            # 기존 프로필 확인
            if existing_service not in list_profile_names():
                return jsonify({"error": f"Existing service '{existing_service}' not found"}), 400

            result = create_reused_profile(existing_service, new_profile_name, port)

            if not result.get("success"):
                return jsonify({"error": result.get("error", "Unknown error")}), 500

            # Reload profiles
            global profiles
            profiles = list_profile_names()

            return jsonify({
                "success": True,
                "profile_name": new_profile_name,
                "editor_dir": result["editor_dir"],
                "message": f"Successfully created reused profile: {new_profile_name}"
            })

        else:
            return jsonify({"error": "Invalid project_type"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

#### 5.1.2 프로필 삭제 API 추가

```python
@app.route("/api/delete-mcp-profile", methods=["DELETE"])
def delete_mcp_profile_api():
    """Delete an MCP profile"""
    try:
        data = request.json or {}
        profile_name = data.get("profile_name", "").strip()

        if not profile_name:
            return jsonify({"error": "profile_name is required"}), 400

        # 원본 프로필 삭제 방지 (보호 대상 프로필 목록)
        protected_profiles = ["outlook", "calendar", "file_handler"]
        if profile_name in protected_profiles:
            return jsonify({"error": f"Cannot delete protected profile: {profile_name}"}), 403

        # 프로필 존재 확인
        if profile_name not in list_profile_names():
            return jsonify({"error": f"Profile '{profile_name}' not found"}), 404

        result = delete_mcp_profile(profile_name)

        if not result.get("success"):
            return jsonify({"error": result.get("error", "Unknown error")}), 500

        # Reload profiles
        global profiles
        profiles = list_profile_names()

        return jsonify({
            "success": True,
            "message": f"Successfully deleted profile: {profile_name}",
            "deleted_paths": result.get("deleted_paths", [])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

#### 5.1.3 사용 가능한 서비스 목록 조회 API 추가

```python
@app.route("/api/available-services", methods=["GET"])
def get_available_services():
    """Get list of available MCP services for reuse"""
    try:
        services = []
        profiles = list_profile_names()

        for profile in profiles:
            profile_conf = get_profile_config(profile)
            source_dir = profile_conf.get("source_dir", "")

            # source_dir이 유효한 프로필만 추가
            if source_dir:
                services.append({
                    "name": profile,
                    "display_name": profile.replace("_", " ").title(),
                    "source_dir": source_dir
                })

        return jsonify({"services": services})
    except Exception as e:
        return jsonify({"error": str(e), "services": []}), 500
```

---

### 5.2 Task 2: 프로필 재사용 생성 함수

**파일**: `/home/kimghw/Connector_auth/mcp_editor/tool_editor_web.py`

```python
def copy_yaml_templates(existing_service: str, new_profile_name: str) -> dict:
    """
    기존 서비스의 YAML 템플릿을 새 프로필로 복사

    Args:
        existing_service: 기존 서비스 이름 (예: "outlook")
        new_profile_name: 새 프로필 이름 (예: "outlook_read")

    Returns:
        {
            "success": bool,
            "yaml_path": str,
            "py_path": str,
            "error": str (실패 시)
        }
    """
    try:
        base_dir = os.path.dirname(__file__)  # mcp_editor/

        # 1. 기존 YAML 파일 경로
        existing_yaml_path = os.path.join(
            base_dir,
            f"mcp_{existing_service}",
            "tool_definition_templates.yaml"
        )

        existing_py_path = os.path.join(
            base_dir,
            f"mcp_{existing_service}",
            "tool_definition_templates.py"
        )

        if not os.path.exists(existing_yaml_path):
            return {
                "success": False,
                "error": f"Template YAML not found: {existing_yaml_path}"
            }

        # 2. 새 프로필 디렉토리 생성
        new_profile_dir = os.path.join(base_dir, f"mcp_{new_profile_name}")
        os.makedirs(new_profile_dir, exist_ok=True)
        os.makedirs(os.path.join(new_profile_dir, "backups"), exist_ok=True)

        # 3. YAML 파일 복사
        new_yaml_path = os.path.join(new_profile_dir, "tool_definition_templates.yaml")
        shutil.copy2(existing_yaml_path, new_yaml_path)

        # 4. Python 로더 파일 복사 (있는 경우)
        new_py_path = os.path.join(new_profile_dir, "tool_definition_templates.py")
        if os.path.exists(existing_py_path):
            shutil.copy2(existing_py_path, new_py_path)
        else:
            # Python 로더 생성
            py_content = '''"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing

이 파일은 tool_definition_templates.yaml을 로드하여 MCP_TOOLS 리스트를 제공합니다.
"""
from typing import List, Dict, Any
from pathlib import Path
import yaml


def _load_tools_from_yaml() -> List[Dict[str, Any]]:
    """YAML 파일에서 도구 정의를 로드합니다."""
    yaml_path = Path(__file__).parent / "tool_definition_templates.yaml"

    if not yaml_path.exists():
        raise FileNotFoundError(f"YAML 파일을 찾을 수 없습니다: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("tools", [])


# 기존 코드와의 호환성을 위해 MCP_TOOLS 리스트 제공
MCP_TOOLS: List[Dict[str, Any]] = _load_tools_from_yaml()
'''
            with open(new_py_path, 'w', encoding='utf-8') as f:
                f.write(py_content)

        return {
            "success": True,
            "yaml_path": new_yaml_path,
            "py_path": new_py_path
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def update_editor_config_for_reuse(
    existing_service: str,
    new_profile_name: str,
    port: int
) -> None:
    """
    editor_config.json에 새 프로필 추가

    Args:
        existing_service: 기존 서비스 이름 (예: "outlook")
        new_profile_name: 새 프로필 이름 (예: "outlook_read")
        port: 새 서버 포트 번호

    Raises:
        KeyError: 기존 서비스 설정이 없을 경우
    """
    base_dir = os.path.dirname(__file__)  # mcp_editor/
    config_path = os.path.join(base_dir, "editor_config.json")

    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    # 기존 설정 참조
    if existing_service not in config:
        raise KeyError(f"Existing service '{existing_service}' not found in editor_config.json")

    existing_conf = config[existing_service]

    # 새 프로필 추가
    config[new_profile_name] = {
        "source_dir": existing_conf["source_dir"],  # 같은 소스 사용!
        "template_definitions_path": f"mcp_{new_profile_name}/tool_definition_templates.py",
        "tool_definitions_path": f"../mcp_{new_profile_name}/mcp_server/tool_definitions.py",
        "backup_dir": f"mcp_{new_profile_name}/backups",
        "types_files": existing_conf.get("types_files", []),  # 같은 타입 사용!
        "host": "0.0.0.0",
        "port": port
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def create_server_project_folder(new_profile_name: str) -> dict:
    """
    서버 프로젝트 폴더 생성 (선택적)

    Args:
        new_profile_name: 새 프로필 이름 (예: "outlook_read")

    Returns:
        {
            "success": bool,
            "project_dir": str,
            "error": str (실패 시)
        }
    """
    try:
        base_dir = os.path.dirname(__file__)  # mcp_editor/
        root_dir = os.path.dirname(base_dir)   # /home/kimghw/Connector_auth/

        # 1. 루트 프로젝트 폴더 생성
        project_dir = os.path.join(root_dir, f"mcp_{new_profile_name}")

        if os.path.exists(project_dir):
            return {
                "success": False,
                "error": f"Project folder mcp_{new_profile_name} already exists"
            }

        os.makedirs(project_dir, exist_ok=True)

        # 2. mcp_server 폴더 생성
        mcp_server_dir = os.path.join(project_dir, "mcp_server")
        os.makedirs(mcp_server_dir, exist_ok=True)

        return {
            "success": True,
            "project_dir": project_dir
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_reused_profile(
    existing_service: str,
    new_profile_name: str,
    port: int
) -> dict:
    """
    기존 서비스를 재사용하는 새 MCP 프로필 생성

    Args:
        existing_service: 기존 서비스 이름 (예: "outlook")
        new_profile_name: 새 프로필 이름 (예: "outlook_read")
        port: 새 서버 포트 번호

    Returns:
        {
            "success": bool,
            "profile_name": str,
            "editor_dir": str,
            "error": str (실패 시)
        }
    """
    try:
        # 1. YAML 템플릿 복사
        yaml_result = copy_yaml_templates(existing_service, new_profile_name)

        if not yaml_result.get("success"):
            return {
                "success": False,
                "error": yaml_result.get("error", "Failed to copy YAML templates")
            }

        # 2. editor_config.json 업데이트
        update_editor_config_for_reuse(existing_service, new_profile_name, port)

        # 3. 서버 프로젝트 폴더 생성 (선택적)
        project_result = create_server_project_folder(new_profile_name)
        # 실패해도 계속 진행 (프로젝트 폴더는 선택적)

        return {
            "success": True,
            "profile_name": new_profile_name,
            "editor_dir": f"mcp_editor/mcp_{new_profile_name}",
            "yaml_path": yaml_result["yaml_path"],
            "py_path": yaml_result["py_path"],
            "project_dir": project_result.get("project_dir", "")
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

---

### 5.3 Task 3: 프로필 삭제 함수

**파일**: `/home/kimghw/Connector_auth/mcp_editor/tool_editor_web.py`

```python
def delete_mcp_profile(profile_name: str) -> dict:
    """
    MCP 프로필 완전 삭제

    삭제 대상:
    - mcp_editor/mcp_{profile}/ 폴더
    - mcp_{profile}/ 폴더 (있는 경우)
    - editor_config.json에서 프로필 제거

    Args:
        profile_name: 프로필 이름 (예: "outlook_read")

    Returns:
        {
            "success": bool,
            "deleted_paths": list,
            "error": str (실패 시)
        }
    """
    try:
        deleted_paths = []
        base_dir = os.path.dirname(__file__)  # mcp_editor/
        root_dir = os.path.dirname(base_dir)   # /home/kimghw/Connector_auth/

        # 1. 에디터 프로필 폴더 삭제
        editor_dir = os.path.join(base_dir, f"mcp_{profile_name}")
        if os.path.exists(editor_dir):
            shutil.rmtree(editor_dir)
            deleted_paths.append(editor_dir)

        # 2. 서버 프로젝트 폴더 삭제 (있는 경우)
        project_dir = os.path.join(root_dir, f"mcp_{profile_name}")
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            deleted_paths.append(project_dir)

        # 3. editor_config.json에서 프로필 제거
        config_path = os.path.join(base_dir, "editor_config.json")

        if os.path.exists(config_path):
            with open(config_path, encoding='utf-8') as f:
                config = json.load(f)

            if profile_name in config:
                del config[profile_name]

                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                deleted_paths.append(f"editor_config.json:{profile_name}")

        return {
            "success": True,
            "deleted_paths": deleted_paths
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

---

### 5.4 Task 4: UI 수정

**파일**: `/home/kimghw/Connector_auth/mcp_editor/templates/tool_editor.html`

#### 5.4.1 Create New MCP Project 모달 수정 (라인 229-272)

**추가 UI - 프로젝트 타입 선택**:
```html
<!-- Service Name 입력 필드 다음에 추가 -->
<div class="form-group">
    <label>Service Name <span style="color: red;">*</span></label>
    <input id="projectServiceName" class="form-control" placeholder="e.g., calendar, weather, database" required>
</div>

<!-- ========== 여기에 새로운 섹션 추가 ========== -->
<div class="form-group">
    <hr style="margin: 20px 0; border-color: #e5e5e5;">
    <label style="font-weight: 600; margin-bottom: 8px; display: block;">
        Project Type
    </label>
    <div style="display: flex; gap: 20px; margin-bottom: 12px;">
        <label style="font-weight: normal;">
            <input type="radio" name="projectType" value="new" checked onchange="toggleReuseOptions()">
            Create from scratch
        </label>
        <label style="font-weight: normal;">
            <input type="radio" name="projectType" value="reuse" onchange="toggleReuseOptions()">
            Reuse existing service
        </label>
    </div>
</div>

<div id="reuseOptions" style="display:none; margin-bottom: 16px;">
    <div class="form-group">
        <label>Existing Service</label>
        <select id="projectReuseService" class="form-control">
            <option value="">-- Select a service to reuse --</option>
            <!-- 동적으로 서비스 목록 로드 -->
        </select>
    </div>
    <div class="form-group">
        <label>New Profile Name <span style="color: red;">*</span></label>
        <input id="projectNewProfileName" class="form-control" placeholder="e.g., outlook_read, calendar_readonly">
        <p style="margin-top: 6px; color: var(--text-secondary); font-size: 12px;">
            The new profile will share the same service code but can have different tools
        </p>
    </div>
</div>
<!-- ============================================= -->
```

#### 5.4.2 프로필 탭에 삭제 버튼 추가

**파일**: `/home/kimghw/Connector_auth/mcp_editor/static/js/tool_editor_ui.js` (또는 관련 JS 파일)

프로필 탭을 동적으로 생성하는 부분에 삭제 버튼 추가:

```javascript
function renderProfileTabs(profiles, activeProfile) {
    const tabsContainer = document.getElementById('profileTabs');
    tabsContainer.innerHTML = '';

    profiles.forEach(profile => {
        const tab = document.createElement('div');
        tab.className = 'profile-tab' + (profile === activeProfile ? ' active' : '');
        tab.innerHTML = `
            <span class="profile-name" onclick="switchProfile('${profile}')">${profile}</span>
            ${!isProtectedProfile(profile) ? `<button class="btn-delete-profile" onclick="deleteProfile('${profile}')" title="Delete profile">×</button>` : ''}
        `;
        tabsContainer.appendChild(tab);
    });
}

function isProtectedProfile(profile) {
    const protected = ['outlook', 'calendar', 'file_handler'];
    return protected.includes(profile);
}

function deleteProfile(profileName) {
    if (!confirm(`Are you sure you want to delete profile "${profileName}"?\n\nThis will delete:\n- mcp_editor/mcp_${profileName}/\n- mcp_${profileName}/ (if exists)\n- Profile from editor_config.json\n\nThis action cannot be undone!`)) {
        return;
    }

    fetch('/api/delete-mcp-profile', {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({profile_name: profileName})
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(`Profile "${profileName}" deleted successfully.\n\nDeleted:\n${data.deleted_paths.join('\n')}`);
            location.reload();
        } else {
            alert('Delete failed: ' + data.error);
        }
    })
    .catch(error => {
        alert('Delete failed: ' + error.message);
    });
}
```

#### 5.4.3 JavaScript 수정 (`tool_editor_tools.js`)

```javascript
function toggleReuseOptions() {
    const projectType = document.querySelector('input[name="projectType"]:checked').value;
    const reuseOptions = document.getElementById('reuseOptions');
    const serviceName = document.getElementById('projectServiceName');

    if (projectType === 'reuse') {
        reuseOptions.style.display = 'block';
        serviceName.disabled = true;
        serviceName.value = '';
        // Load available services
        loadAvailableServices();
    } else {
        reuseOptions.style.display = 'none';
        serviceName.disabled = false;
    }
}

async function loadAvailableServices() {
    try {
        const response = await fetch('/api/available-services');
        const data = await response.json();

        const selectEl = document.getElementById('projectReuseService');
        selectEl.innerHTML = '<option value="">-- Select a service to reuse --</option>';

        data.services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.name;
            option.textContent = `${service.display_name} (${service.source_dir})`;
            selectEl.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load available services:', error);
    }
}

function createNewProject() {
    const projectType = document.querySelector('input[name="projectType"]:checked').value;
    const port = parseInt(document.getElementById('projectPort').value) || 8080;

    let requestBody = { port };

    if (projectType === 'new') {
        // 기존 로직
        const serviceName = document.getElementById('projectServiceName').value.trim();
        const description = document.getElementById('projectDescription').value.trim();
        const author = document.getElementById('projectAuthor').value.trim();
        const includeTypes = document.getElementById('projectIncludeTypes').checked;

        if (!serviceName) {
            alert('Service name is required');
            return;
        }

        requestBody = {
            project_type: 'new',
            service_name: serviceName,
            description: description,
            port: port,
            author: author,
            include_types: includeTypes
        };
    } else if (projectType === 'reuse') {
        // 재사용 로직
        const existingService = document.getElementById('projectReuseService').value;
        const newProfileName = document.getElementById('projectNewProfileName').value.trim();

        if (!existingService) {
            alert('Please select an existing service');
            return;
        }

        if (!newProfileName) {
            alert('New profile name is required');
            return;
        }

        if (!/^[a-zA-Z0-9_]+$/.test(newProfileName)) {
            alert('Profile name can only contain letters, numbers, and underscores');
            return;
        }

        requestBody = {
            project_type: 'reuse',
            existing_service: existingService,
            new_profile_name: newProfileName,
            port: port
        };
    }

    const resultEl = document.getElementById('createProjectResult');
    resultEl.style.display = 'block';
    resultEl.style.backgroundColor = '#e3f2fd';
    resultEl.textContent = 'Creating project...';

    fetch('/api/create-mcp-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            resultEl.style.backgroundColor = '#e8f5e9';

            let message = `<strong>✅ Success!</strong><br>`;
            if (projectType === 'new') {
                message += `Created project: ${data.project_dir}<br>`;
                message += `Files created: ${data.created_files}<br><br>`;
            } else {
                message += `Created reused profile: ${data.profile_name}<br>`;
                message += `Editor directory: ${data.editor_dir}<br><br>`;
            }
            message += `<strong>Next steps:</strong><br>`;
            message += `1. Reload this page to see the new profile<br>`;
            message += `2. Select the profile from the profile tabs<br>`;
            if (projectType === 'reuse') {
                message += `3. Edit tools (delete unwanted tools)<br>`;
                message += `4. Click "Generate Server" to create server files<br>`;
            }

            resultEl.innerHTML = message;

            // Reload profiles after 3 seconds
            setTimeout(() => {
                location.reload();
            }, 3000);
        } else {
            resultEl.style.backgroundColor = '#ffebee';
            resultEl.innerHTML = `<strong>❌ Error:</strong> ${data.error}`;
        }
    })
    .catch(error => {
        resultEl.style.backgroundColor = '#ffebee';
        resultEl.innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
    });
}
```

---

## 6. 테스트 시나리오

### 6.1 서비스 재사용 생성 테스트

#### 6.1.1 프로필 생성

```bash
# 1. 웹에디터 접속
http://localhost:8091

# 2. Create New MCP Project 클릭
# - Project Type: "Reuse existing service" 선택
# - Existing Service: "outlook"
# - New Profile Name: "outlook_read"
# - Port: 8092
# - Create Project 클릭
```

#### 6.1.2 생성 확인

```bash
# 에디터 프로필 폴더 확인
ls -la /home/kimghw/Connector_auth/mcp_editor/mcp_outlook_read/

# 예상 출력:
# mcp_outlook_read/
# ├── tool_definition_templates.yaml   (outlook에서 복사됨)
# ├── tool_definition_templates.py
# └── backups/

# editor_config.json 확인
cat /home/kimghw/Connector_auth/mcp_editor/editor_config.json | jq '.outlook_read'

# 예상 출력:
# {
#   "source_dir": "../mcp_outlook",  <- outlook과 같음
#   "template_definitions_path": "mcp_outlook_read/tool_definition_templates.py",
#   "tool_definitions_path": "../mcp_outlook_read/mcp_server/tool_definitions.py",
#   "backup_dir": "mcp_outlook_read/backups",
#   "types_files": ["../mcp_outlook/outlook_types.py"],  <- outlook과 같음
#   "host": "0.0.0.0",
#   "port": 8092
# }
```

#### 6.1.3 도구 편집 및 서버 생성

```bash
# 1. 웹에디터에서 프로필 선택: outlook_read
http://localhost:8091?profile=outlook_read

# 2. 불필요한 도구 삭제 (11개 → 6개로 줄임)
# - 삭제할 도구 예시: mail_attachment_download, mail_process_with_download 등

# 3. Generate Server 클릭
# - Protocol: REST 선택
# - Generate 클릭

# 4. 생성된 서버 확인
ls -la /home/kimghw/Connector_auth/mcp_outlook_read/mcp_server/

# 예상 출력:
# server_rest.py
# server_init.py
# run.py
# ...
```

#### 6.1.4 서버 실행 및 테스트

```bash
# 서버 실행
cd /home/kimghw/Connector_auth/mcp_outlook_read/mcp_server
python run.py

# 도구 목록 확인
curl http://localhost:8092/tools/list | jq '.tools[].name'

# 예상 출력: 6개 도구만 노출됨
```

### 6.2 프로필 삭제 테스트

```bash
# 1. 웹에디터에서 프로필 탭의 X 버튼 클릭
# 2. 확인 팝업에서 확인
# 3. 삭제 결과 확인

# 에디터 폴더 삭제 확인
ls /home/kimghw/Connector_auth/mcp_editor/mcp_outlook_read/  # 없어야 함

# 서버 폴더 삭제 확인
ls /home/kimghw/Connector_auth/mcp_outlook_read/  # 없어야 함

# editor_config.json 확인
cat /home/kimghw/Connector_auth/mcp_editor/editor_config.json | jq '.outlook_read'  # null이어야 함
```

### 6.3 보호된 프로필 삭제 방지 테스트

```bash
# 원본 프로필 삭제 시도 (outlook, calendar, file_handler)
curl -X DELETE http://localhost:8091/api/delete-mcp-profile \
  -H "Content-Type: application/json" \
  -d '{"profile_name": "outlook"}'

# 예상 응답:
# {
#   "error": "Cannot delete protected profile: outlook"
# }
# Status: 403 Forbidden
```

---

## 7. 파일 수정 목록

### 7.1 선행 수정 사항 (섹션 0)

| 파일 | 수정 내용 | 우선순위 | 상태 |
|------|----------|---------|------|
| [tool_editor_tools.js](../../mcp_editor/static/js/tool_editor_tools.js) | `createNewProject()` 중복 제거 (Line 528) | 🔴 선행 | 🔴 구현 필요 |
| [mcp_server_controller.py](../../mcp_editor/mcp_server_controller.py) | `_get_server_path()` editor_config.json 기반으로 수정 | 🔴 필수 | 🔴 구현 필요 |
| [universal_server_template.jinja2](../../jinja/universal_server_template.jinja2) | YAML 경로 상대 경로로 수정 (Line 103) | 🔴 필수 | 🔴 구현 필요 |
| [universal_server_template.jinja2](../../jinja/universal_server_template.jinja2) | 포트 변수화 (Line 728) | 🟡 중요 | 🔴 구현 필요 |
| [generate_editor_config.py](../../jinja/generate_editor_config.py) | merge 전략 추가 (기존 프로필 보존) | 🟡 중요 | 🔴 구현 필요 |
| [tool_editor_web.py](../../mcp_editor/tool_editor_web.py) | `discover_mcp_modules()` 경로 로직 수정 (Line 337) | 🟡 중요 | 🔴 구현 필요 |

### 7.2 본 기능 구현 (섹션 5)

| 파일 | 수정 내용 | 상태 |
|------|----------|------|
| [tool_editor_web.py](../../mcp_editor/tool_editor_web.py) | `copy_yaml_templates()` 함수 추가 | 🔴 구현 필요 |
| [tool_editor_web.py](../../mcp_editor/tool_editor_web.py) | `update_editor_config_for_reuse()` 함수 추가 | 🔴 구현 필요 |
| [tool_editor_web.py](../../mcp_editor/tool_editor_web.py) | `create_server_project_folder()` 함수 추가 | 🔴 구현 필요 |
| [tool_editor_web.py](../../mcp_editor/tool_editor_web.py) | `create_reused_profile()` 함수 추가 | 🔴 구현 필요 |
| [tool_editor_web.py](../../mcp_editor/tool_editor_web.py) | `delete_mcp_profile()` 함수 추가 | 🔴 구현 필요 |
| [tool_editor_web.py](../../mcp_editor/tool_editor_web.py) | `/api/create-mcp-project` 엔드포인트 수정 | 🔴 구현 필요 |
| [tool_editor_web.py](../../mcp_editor/tool_editor_web.py) | `/api/delete-mcp-profile` 엔드포인트 추가 | 🔴 구현 필요 |
| [tool_editor_web.py](../../mcp_editor/tool_editor_web.py) | `/api/available-services` 엔드포인트 추가 | 🔴 구현 필요 |
| [tool_editor.html](../../mcp_editor/templates/tool_editor.html) | 프로젝트 타입 선택 UI 추가 | 🔴 구현 필요 |
| [tool_editor_tools.js](../../mcp_editor/static/js/tool_editor_tools.js) | `toggleReuseOptions()`, `loadAvailableServices()` 함수 추가 | 🔴 구현 필요 |
| [tool_editor_tools.js](../../mcp_editor/static/js/tool_editor_tools.js) | `createNewProject()` 함수 수정 (재사용 로직 추가) | 🔴 구현 필요 |
| [tool_editor_ui.js](../../mcp_editor/static/js/tool_editor_ui.js) | `renderProfileTabs()`, `deleteProfile()` 함수 추가 | 🔴 구현 필요 |

---

## 8. 생성되는 디렉토리 구조

```
/home/kimghw/Connector_auth/
├── mcp_outlook/                          # 원본 서비스
│   ├── outlook_service.py
│   ├── outlook_types.py
│   └── mcp_server/
│       └── server_rest.py                # 11개 도구
│
├── mcp_outlook_read/                     # 신규: 조회 전용 (재사용)
│   └── mcp_server/
│       └── server_rest.py                # 6개 도구만
│
├── mcp_outlook_process/                  # 신규: 처리 전용 (재사용)
│   └── mcp_server/
│       └── server_rest.py                # 5개 도구만
│
└── mcp_editor/
    ├── editor_config.json                # 3개 프로필: outlook, outlook_read, outlook_process
    │
    ├── mcp_service_registry/             # Registry 중앙 저장소 ✅
    │   └── registry_outlook.json         # outlook 서비스 메타데이터 (공유)
    │
    ├── mcp_outlook/                      # outlook 프로필 YAML
    │   ├── tool_definition_templates.yaml   # 11개
    │   └── tool_definition_templates.py
    │
    ├── mcp_outlook_read/                 # outlook_read 프로필 YAML (복사본)
    │   ├── tool_definition_templates.yaml   # 6개 (편집 후)
    │   └── tool_definition_templates.py
    │
    └── mcp_outlook_process/              # outlook_process 프로필 YAML (복사본)
        ├── tool_definition_templates.yaml   # 5개 (편집 후)
        └── tool_definition_templates.py
```

**공유 자원**:
- `mcp_outlook/outlook_service.py` ← 모든 프로필이 참조 (source_dir 동일)
- `mcp_outlook/outlook_types.py` ← 모든 프로필이 참조 (types_files 동일)
- `mcp_editor/mcp_service_registry/registry_outlook.json` ← 중앙 메타데이터

---

## 9. 주의사항

### 9.1 프로필 재사용

- ✅ **같은 source_dir 사용**: 모든 재사용 프로필은 원본 서비스 코드를 참조
- ✅ **YAML 독립성**: 각 프로필은 독립적인 YAML 템플릿을 가지므로 도구 편집 가능
- ⚠️ **원본 서비스 수정 영향**: 원본 서비스 코드를 수정하면 모든 재사용 프로필에 영향

### 9.2 삭제 작업

- ⚠️ 삭제는 복구 불가능하므로 확인 팝업 필수
- ⚠️ 원본 프로필 (outlook, calendar, file_handler) 삭제 방지 로직 필수
- ✅ backups/ 폴더도 함께 삭제됨

### 9.3 포트 관리

- 각 프로필은 고유한 포트 사용
- 기존 포트와 충돌 방지 확인 필요

### 9.4 Registry 중앙 관리

- Registry 파일은 `mcp_editor/mcp_service_registry/`에 중앙 집중식으로 관리
- 재사용 프로필은 새 Registry를 생성하지 않고 기존 Registry를 참조
- `@mcp_service` 데코레이터로 자동 생성되는 Registry는 원본 서비스에만 존재

---

## 10. usersenario.md 기록 항목

```markdown
### 2026-01-10: 기존 서비스 재사용 MCP 프로필 생성 및 삭제 기능 구현

#### 요청 사항
- 기존 MCP 서비스를 재사용하여 도구 세트가 다른 새 프로필 생성
- YAML 템플릿 복사 방식으로 독립적인 도구 관리
- MCP 프로필 삭제 기능 추가

#### 구현 완료 항목

**1. YAML 템플릿 복사 방식**
- `copy_yaml_templates()`: 기존 프로필의 YAML을 새 프로필로 복사
- editor_config.json에서 같은 source_dir 참조 (코드 재사용)
- 중앙 Registry 관리 (mcp_editor/mcp_service_registry/)

**2. 프로필 재사용 생성**
- `create_reused_profile()`: 새 프로필 생성, YAML 복사, editor_config.json 업데이트
- `update_editor_config_for_reuse()`: 기존 source_dir, types_files 재사용하는 프로필 추가
- `/api/create-mcp-project` API 확장: project_type="reuse" 지원

**3. 프로필 삭제**
- `delete_mcp_profile()`: mcp_editor/mcp_{profile}/ 폴더, editor_config.json 프로필 완전 삭제
- `/api/delete-mcp-profile` API 추가
- 원본 프로필 (outlook, calendar, file_handler) 삭제 방지
- UI에 삭제 버튼 추가 (프로필 탭 X 버튼)

#### 사용 예시
```
기존: outlook (11개 도구, mcp_outlook 참조)
    ↓ 재사용 생성
신규: outlook_read (YAML 복사 → 6개만 선택, mcp_outlook 참조)
    ↓ 삭제
삭제: outlook_read 프로필 완전 제거
```

#### 장점
- 같은 서비스 로직 재사용 (코드 중복 없음)
- 권한 분리 (도구별 프로필 분리)
- 중앙 Registry 관리 (mcp_editor/mcp_service_registry/)
- 독립적인 YAML 관리 (각 프로필별 도구 편집 가능)
- 불필요한 프로필 쉽게 삭제

#### 수정된 파일
- `mcp_editor/tool_editor_web.py`: 5개 함수 + 3개 API 엔드포인트
- `mcp_editor/templates/tool_editor.html`: UI 추가 (프로젝트 타입 선택)
- `mcp_editor/static/js/tool_editor_tools.js`: 재사용 로직 추가
- `mcp_editor/static/js/tool_editor_ui.js`: 삭제 버튼 추가
```

---

*Last Updated: 2026-01-10*
*Version: 4.0 (선행 수정 사항 추가)*
