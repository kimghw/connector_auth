---
name: mcp-setup
description: >-
  Use when converting an existing Python project into an MCP server via the web editor:
  create an mcp_{server} folder, build a facade service.py with @mcp_service, auto-pick
  key functions to expose, seed tool_definition_templates.py with defaults, and wire
  editor_config.json so the tool editor can generate tool_definitions.py/server.py.
---

# MCP Setup with the Web Editor

> **핵심 목적**: 기존 프로젝트에 **웹 에디터를 연결**하여 MCP 핸들러(도구 스키마, 파라미터, 설명 등)를 **GUI로 편집/관리**할 수 있게 설정합니다. 단순히 MCP 서버를 만드는 것이 아니라, 런타임에 도구 정의를 시각적으로 수정하고 재생성할 수 있는 관리 인프라를 구축합니다.

Goal: turn an existing project into an MCP server the web editor can manage (decorators → registry → tool templates → generated server).

---

## Step 0: 인프라 가져오기 (필수)

스킬 실행 전, 아래 인프라 파일들을 GitHub에서 가져와야 합니다.

### 가져올 파일/폴더 (코어)

```
mcp_editor/
├── tool_editor_web.py              # 웹 에디터 메인
├── tool_editor_core/               # 라우트 및 유틸리티 (전체)
├── mcp_service_registry/
│   ├── mcp_service_decorator.py    # @mcp_service 데코레이터
│   ├── mcp_service_scanner.py      # 서비스 스캐너
│   ├── extract_types.py
│   ├── meta_registry.py
│   └── pydantic_to_schema.py
├── static/                         # CSS, JS (전체)
├── templates/                      # HTML 템플릿 (전체)
├── pydantic_to_schema.py
├── extract_graph_types.py
├── generate_editor_config.py
└── mcp_server_controller.py

jinja/
├── generate_universal_server.py    # 서버 생성기
├── generate_editor_config.py
├── *.jinja2                        # 템플릿 파일들
└── (backup/, legacy_backup/ 제외)

.claude/skills/mcp-setup/           # 이 스킬 (전체)
```

### 제외할 파일 (프로젝트별 데이터)

```
mcp_editor/mcp_*/                   # mcp_outlook, mcp_calendar 등
mcp_editor/editor_config.json       # 프로젝트별 설정
mcp_editor/mcp_service_registry/registry_*.json
mcp_editor/mcp_service_registry/types_property_*.json
jinja/backup/
jinja/legacy_backup/
*/__pycache__/
```

### 가져오기 명령어

```bash
# GitHub에서 sparse-checkout으로 가져오기
REPO_URL="https://github.com/USER/Connector_auth.git"
TARGET_DIR="/path/to/your/project"

# 임시 클론
git clone --filter=blob:none --sparse $REPO_URL _infra_temp
cd _infra_temp
git sparse-checkout set mcp_editor jinja .claude/skills/mcp-setup

# 코어 파일만 복사
cp -r mcp_editor $TARGET_DIR/
cp -r jinja $TARGET_DIR/
mkdir -p $TARGET_DIR/.claude/skills
cp -r .claude/skills/mcp-setup $TARGET_DIR/.claude/skills/

# 프로젝트별 데이터 정리
cd $TARGET_DIR
rm -rf mcp_editor/mcp_*/
rm -f mcp_editor/editor_config.json
rm -f mcp_editor/mcp_service_registry/registry_*.json
rm -f mcp_editor/mcp_service_registry/types_property_*.json
rm -rf jinja/backup jinja/legacy_backup
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# 임시 폴더 정리
cd .. && rm -rf _infra_temp

echo "인프라 설치 완료"
```

### 확인 체크리스트

- [ ] `mcp_editor/tool_editor_web.py` 존재
- [ ] `mcp_editor/tool_editor_core/` 존재
- [ ] `mcp_editor/mcp_service_registry/mcp_service_decorator.py` 존재
- [ ] `jinja/generate_universal_server.py` 존재
- [ ] `.claude/skills/mcp-setup/SKILL.md` 존재

위 파일들이 모두 존재하면 다음 단계로 진행합니다.

---

## Quick start
- Pick a server name (e.g., `demo`) and mirror/rename the project to `mcp_demo/`.
- Drop a facade file (`service.py` or `demo_service.py`) using `references/service_facade_template.py` and add `@mcp_service` to each exported function.
- Seed `mcp_editor/mcp_demo/tool_definition_templates.py` from `references/tool_definition_templates_sample.py` so the web editor has defaults.
- Add a `mcp_demo` profile block to `mcp_editor/editor_config.json` (see `references/editor_config_snippet.json`).
- Run `python mcp_editor/tool_editor_web.py`, verify auto-scan picked up the decorators, adjust schemas, then Save to emit `tool_definitions.py`.
- Generate the server when ready: `python jinja/generate_universal_server.py demo` (do not hand-edit generated files).

## Pre-setup Interview (Required)

Before starting mcp_setup, you MUST complete the following interview process with the user.

### Step A: Project Analysis

1. **Assess Project Scale**
   - Count the number of Python files in the project (`*.py` file scan)
   - Identify main modules and package structure
   - Locate existing service functions and business logic

2. **Check for Existing MCP/Handler Implementation**
   - Check for existing MCP server folders (`mcp_*/` pattern)
   - Check for handler files (`*_handler.py`, `handler.py` patterns)
   - Check for existing `tool_definitions.py`, `server.py` files
   - Check `mcp_editor/mcp_service_registry/registry_*.json` files

### Step B: Determine Handling Policy for Existing Implementation

If existing MCP servers or handlers are found:

1. **Present Options to User** (use AskUserQuestion)
   - **Option 1: Remove and Rebuild**
     - Delete all existing handlers and MCP-related scripts
     - Set up fresh with new structure
   - **Option 2: Keep Existing Implementation and Document**
     - Record existing handler info in `mcp_editor/mcp_{server}/existing_handlers_log.md`
     - Document: handler names, service functions used, mapping info
     - Manage alongside new setup
   - **Option 3: Convert Existing Implementation to Service Functions**
     - Migrate existing MCP tools/handlers to `@mcp_service` decorator-based service functions
     - Wrap existing logic using the facade pattern

### Step C: Determine MCP Server Structure

1. **Decide Number of Servers** (use AskUserQuestion)

   | Project Scale | Recommended Structure | Description |
   |--------------|----------------------|-------------|
   | Small (< 20 files) | Single MCP Server | Create 1 pair of `*_service.py`, `*_types.py`. Can use derived feature later to categorize handlers |
   | Medium (20-100 files) | Single or Multiple MCP Servers | User choice whether to split by domain |
   | Large (> 100 files) | Multiple MCP Servers | Create multiple `*_service.py`, `*_types.py` pairs by domain to separate MCP servers |

2. **Server Structure Options Explained**
   - **Single Server (1)**: Easier to manage; can logically categorize handlers later using the derived feature
   - **Multiple Servers (2+)**: Create `{domain}_service.py`, `{domain}_types.py` pairs per domain for independent MCP server operation

3. **Multi-Project Merge** (Informational Only)
   > **Under Development**: The feature to consolidate 2+ projects into a single MCP server is currently being developed. Manual configuration is possible if needed.

### Step D: Interview Checklist

Items to confirm before proceeding:

- [ ] Project file count analysis complete
- [ ] Existing MCP server/handler check complete
- [ ] Existing implementation handling policy decided (remove/keep/convert)
- [ ] MCP server count decided (single/multiple)
- [ ] Server name(s) confirmed
- [ ] Candidate list of service functions to expose prepared

### Step E: Existing Implementation Log Template (if keeping)

Create `mcp_editor/mcp_{server}/existing_handlers_log.md`:

```markdown
# Existing MCP Handler Log

## Analysis Date
- Date: YYYY-MM-DD

## Existing Handler List

### Handler: {handler_name}
- File Location: {file_path}
- Service Functions Used:
  - `{function_name}` from `{module_path}`
- Mapped MCP Tool: {tool_name}
- Notes: {notes}

## Migration Plan
- [ ] {handler_name} → {new_service_function}
```

---

## Workflow
0) Verify prerequisites
- **Check required folders first**: Before starting, verify that all required infrastructure folders exist. See `references/required_folders.md` for the full list.
- Required folders: `.claude/skills/mcp-setup/`, `.claude/commands/`, `mcp_editor/`, `mcp_editor/mcp_service_registry/`, `jinja/`
- If any folder is missing, inform the user that they need to copy the MCP infrastructure from a configured project.

1) Prepare the target project
- Normalize naming: folders and editor config keys should be `mcp_{server}`. Place server code under `mcp_{server}/mcp_server/`.
- Keep business logic importable by the facade (no heavy side effects on import; move those behind functions).

2) Select functions to expose (agent-assisted)
- **Review the project first**: Analyze the codebase structure, identify core business logic, and understand the domain before proposing services.
- **Propose candidate services**: Present a ranked list of functions suitable for MCP exposure to the user, explaining why each was selected (importance, frequency of use, API suitability).
- **Get user feedback**: Ask the user to confirm, modify, or add to the proposed list before proceeding. Use AskUserQuestion to clarify priorities or resolve ambiguities.
- Scan for public, side-effect-safe entry points that return serializable data or clear status (controllers, service layer, use-cases). Prefer functions with simple parameters over deeply coupled internals.
- Extract docstrings/comments for descriptions and note default values/Optional hints. Avoid exposing constructors or low-level helpers unless necessary.

3) Build the service class with decorators

> **중요**: 서비스 파일은 반드시 **클래스 기반**으로 작성합니다. 함수 기반이 아닌 클래스로 구성해야 의존성 주입, 상태 관리, 테스트가 용이합니다.

#### 3.1 프로젝트 분석 (필수)
서비스 클래스 작성 전, 기존 프로젝트의 구조를 분석합니다:
- **핵심 모듈 식별**: 비즈니스 로직이 있는 모듈/클래스 파악
- **의존성 분석**: 외부 서비스, DB 연결, API 클라이언트 등 확인
- **데이터 흐름 파악**: 입력 → 처리 → 출력 흐름 이해
- **기존 패턴 확인**: 프로젝트에서 사용 중인 디자인 패턴 파악

#### 3.2 서비스 클래스 작성
- `references/service_facade_template.py`를 참고하여 `mcp_{server}/{server}_service.py` 생성
- **클래스 구조 필수**: `class {Server}Service:` 형태로 작성
- 각 메서드에 `@mcp_service(tool_name=..., server_name=..., service_name=..., description=..., tags=..., category=...)` 데코레이터 적용
- 생성자(`__init__`)에서 의존성 초기화 (DB 연결, API 클라이언트 등)

#### 3.3 클래스 설계 원칙
```python
class DemoService:
    """서비스 클래스 - 모든 MCP 도구의 진입점"""

    def __init__(self):
        # 의존성 초기화 (한 번만 실행)
        self._client = SomeClient()
        self._cache = {}

    @mcp_service(tool_name="list_items", ...)
    def list_items(self, filter: str = None) -> List[dict]:
        # 실제 비즈니스 로직 호출
        return self._client.get_items(filter)
```

- **JSON 직렬화 가능한 반환값** 유지
- 복잡한 타입이 필요하면 `{server}_types.py`에 Pydantic 모델 정의
- 모듈 임포트 시 I/O 작업 금지 (생성자에서 처리)
- 웹 에디터는 `types_files` 설정을 통해 타입 모델의 속성 정보를 추출

4) Register services
- Launch the web editor (`python mcp_editor/tool_editor_web.py`) to auto-scan `@mcp_service` and refresh `registry_{server}.json`, or run `python mcp_editor/mcp_service_registry/mcp_service_scanner.py` directly.
- Confirm the registry entry shows `tool_name`, `server_name`, and the correct implementation module/method.

5) Seed tool templates (LLM-facing schemas)
- **Create YAML loader**: Write `mcp_editor/mcp_{server}/tool_definition_templates.py` as a simple YAML loader (see `references/tool_definition_templates_sample.py`). This .py file loads the YAML and exports `MCP_TOOLS` list for web editor compatibility.
- **Ask user preference**: Before writing `tool_definition_templates.yaml`, ask the user:
  - **Interactive mode**: Interview the user about each tool's purpose, required vs optional params, descriptions, and internal defaults. Creates more tailored schemas.
  - **Auto mode**: Agent analyzes `{server}_service.py` and generates initial schemas based on function signatures, docstrings, and type hints. Faster but may need refinement in web editor.
- Use `mcp_editor/mcp_service_registry/mcp_service_decorator.generate_inputschema_from_service` if you want to auto-derive a starting `inputSchema` from the captured signature; then refine descriptions and required fields.
- Keep `MCP_TOOLS` in sync with the facade: names, signatures, and targetParam mappings should mirror the `@mcp_service` parameters. Include at least one default entry so the editor UI is not empty.

6) Wire the web editor profile
- Add a profile block in `mcp_editor/editor_config.json` keyed by `mcp_{server}`: template path, output path, optional `types_files`, and port/host. Use `references/editor_config_snippet.json` as a shape guide.
- If you prefer templating, regenerate via `python jinja/generate_editor_config.py` after editing the template.

7) Generate and validate
- In the web editor, adjust schemas/internal args as needed and click Save to write `mcp_{server}/mcp_server/tool_definitions.py`.
- Generate the server scaffold when ready: `python jinja/generate_universal_server.py {server}`. Do not edit generated `server.py` or `tool_definitions.py` directly; modify templates/facades instead.
- Smoke test: `python mcp_{server}/mcp_server/server.py` then invoke one tool manually to confirm wiring.

8) Final verification checklist
Before completing, verify all artifacts were created:
- [ ] `mcp_{server}/{server}_service.py` exists with `@mcp_service` decorators
- [ ] `mcp_{server}/{server}_types.py` exists (if complex types are used)
- [ ] `mcp_editor/mcp_{server}/tool_definition_templates.py` exists (YAML loader)
- [ ] `mcp_editor/mcp_{server}/tool_definition_templates.yaml` exists **and contains at least one tool definition** (not empty)
- [ ] `mcp_editor/mcp_{server}/backups/` directory exists
- [ ] `mcp_editor/editor_config.json` has the `{server}` profile
- [ ] `mcp_editor/mcp_service_registry/registry_{server}.json` exists
- If any item is missing or empty, complete it before finishing.

## Agent notes for auto-extraction

### 분석 우선 원칙
- **프로젝트 분석 먼저**: 서비스 클래스 작성 전 반드시 기존 프로젝트 구조를 분석
- **핵심 모듈 파악**: 비즈니스 로직이 집중된 모듈, 클래스, 함수 식별
- **의존성 맵핑**: 외부 서비스, DB, API 클라이언트 등 의존성 목록화
- **패턴 이해**: 기존 프로젝트의 아키텍처 패턴 파악 (MVC, Clean Architecture 등)

### 서비스 클래스 생성 규칙
- **반드시 클래스 기반**: `class {Server}Service:` 형태로 작성 (함수 기반 금지)
- **생성자에서 의존성 초기화**: `__init__`에서 클라이언트, 연결 등 설정
- **메서드별 데코레이터**: 각 공개 메서드에 `@mcp_service` 적용
- **self 파라미터 유지**: 클래스 메서드이므로 첫 번째 인자는 항상 `self`

### 비즈니스 가치 우선
- **Prioritize business value**: Identify the most important business logic first. Focus on functions that users will call frequently or that provide unique value.
- **Generate artifacts**: After user confirmation, the agent MUST create:
  1. `{server}_service.py` with **class-based structure** and `@mcp_service` decorators
  2. Initial `tool_definition_templates.yaml` with LLM-facing schemas for key tools
- Use heuristics to rank candidate functions: high-level orchestration, minimal side effects, good docstrings, and parameters that map cleanly to JSON. Skip functions requiring global state unless you can inject dependencies in the service class.
- When unsure about parameter schemas, default to strings and mark optional; let the web editor refine types. Populate `description` from docstrings/comments.
- Always add a couple of safe defaults (health/ping, list/sample) in `tool_definition_templates.yaml` so users see working examples immediately.
- **Iterative refinement**: After initial setup, ask the user if they want to add more services or adjust priorities.

## References to load when needed
- `.claude/skills/mcp-setup/references/required_folders.md` — **prerequisite check**: folders that must exist before running this skill.
- `.claude/skills/mcp-setup/references/service_facade_template.py` — facade + decorator usage example.
- `.claude/skills/mcp-setup/references/tool_definition_templates_sample.py` — minimal MCP_TOOLS template (Python loader).
- `.claude/skills/mcp-setup/references/tool_definition_templates_sample.yaml` — **annotated YAML template** with detailed comments explaining data flow, field sources, and call paths.
- `.claude/skills/mcp-setup/references/editor_config_snippet.json` — profile block shape for `mcp_{server}`.
- Project docs: `mcp_editor/tool_editor_web.py`, `.claude/commands/web-editor.md`, `.claude/commands/terminology.md`, `mcp_editor/mcp_service_registry/mcp_service_decorator.py` for decorator details.
