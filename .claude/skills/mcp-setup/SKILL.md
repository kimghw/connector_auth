---
name: mcp-setup
description: >-
  Use when converting an existing Python project into an MCP server via the web editor:
  create an mcp_{server} folder, build a facade service.py with @mcp_service, auto-pick
  key functions to expose, seed tool_definition_templates.py with defaults, and wire
  editor_config.json so the tool editor can generate tool_definitions.py/server.py.
---

# MCP Setup with the Web Editor

Goal: turn an existing project into an MCP server the web editor can manage (decorators → registry → tool templates → generated server).

## Quick start
- Pick a server name (e.g., `demo`) and mirror/rename the project to `mcp_demo/`.
- Drop a facade file (`service.py` or `demo_service.py`) using `references/service_facade_template.py` and add `@mcp_service` to each exported function.
- Seed `mcp_editor/mcp_demo/tool_definition_templates.py` from `references/tool_definition_templates_sample.py` so the web editor has defaults.
- Add a `mcp_demo` profile block to `mcp_editor/editor_config.json` (see `references/editor_config_snippet.json`).
- Run `python mcp_editor/tool_editor_web.py`, verify auto-scan picked up the decorators, adjust schemas, then Save to emit `tool_definitions.py`.
- Generate the server when ready: `python jinja/generate_universal_server.py demo` (do not hand-edit generated files).

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

3) Build the facade with decorators
- Start from `references/service_facade_template.py`; copy to `mcp_{server}/{server}_service.py` (or `service.py`).
- For each exposed function, wrap the underlying call and annotate with `@mcp_service(tool_name=..., server_name=..., service_name=..., description=..., tags=..., category=...)`.
- Keep return values JSON-serializable. If you need richer types for parameters or return values, define Pydantic models in `{server}_types.py` and import them. The web editor uses `types_files` config to extract property information from these models for internal parameter configuration.
- Prefer pure wrappers so scanning stays stable; avoid doing I/O at module import time.

4) Register services
- Launch the web editor (`python mcp_editor/tool_editor_web.py`) to auto-scan `@mcp_service` and refresh `registry_{server}.json`, or run `python mcp_editor/mcp_service_registry/mcp_service_scanner.py` directly.
- Confirm the registry entry shows `tool_name`, `server_name`, and the correct implementation module/method.

5) Seed tool templates (LLM-facing schemas)
- Copy `references/tool_definition_templates_sample.py` to `mcp_editor/mcp_{server}/tool_definition_templates.py` and align entries with your decorated functions.
- Use `mcp_editor/mcp_service_registry/mcp_service_decorator.generate_inputschema_from_service` if you want to auto-derive a starting `inputSchema` from the captured signature; then refine descriptions and required fields.
- Keep `MCP_TOOLS` in sync with the facade: names, signatures, and targetParam mappings should mirror the `@mcp_service` parameters. Include at least one default entry so the editor UI is not empty.

6) Wire the web editor profile
- Add a profile block in `mcp_editor/editor_config.json` keyed by `mcp_{server}`: template path, output path, optional `types_files`, and port/host. Use `references/editor_config_snippet.json` as a shape guide.
- If you prefer templating, regenerate via `python jinja/generate_editor_config.py` after editing the template.

7) Generate and validate
- In the web editor, adjust schemas/internal args as needed and click Save to write `mcp_{server}/mcp_server/tool_definitions.py`.
- Generate the server scaffold when ready: `python jinja/generate_universal_server.py {server}`. Do not edit generated `server.py` or `tool_definitions.py` directly; modify templates/facades instead.
- Smoke test: `python mcp_{server}/mcp_server/server.py` then invoke one tool manually to confirm wiring.

## Agent notes for auto-extraction
- **Prioritize business value**: Identify the most important business logic first. Focus on functions that users will call frequently or that provide unique value.
- **Generate artifacts**: After user confirmation, the agent MUST create:
  1. `{server}_service.py` with `@mcp_service` decorators for approved functions
  2. Initial `tool_definition_templates.yaml` with LLM-facing schemas for key tools
- Use heuristics to rank candidate functions: high-level orchestration, minimal side effects, good docstrings, and parameters that map cleanly to JSON. Skip functions requiring global state unless you can inject dependencies in the facade.
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
