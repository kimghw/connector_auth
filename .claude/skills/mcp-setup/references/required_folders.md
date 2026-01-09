# MCP Setup 스킬 적용을 위한 필수 폴더

다른 프로젝트에 mcp-setup 스킬을 적용하려면 아래 폴더들을 복사해야 합니다.

## 복사 필수 폴더

```
project_root/
├── .claude/
│   ├── skills/
│   │   └── mcp-setup/            # 스킬 정의 및 참조 파일
│   └── commands/
│       ├── web-editor.md         # 웹에디터 가이드
│       └── terminology.md        # 용어 정의
│
├── mcp_editor/                   # 웹에디터 코어
│   ├── tool_editor_web.py
│   ├── editor_config.json
│   ├── mcp_service_registry/     # 데코레이터 + 스캐너
│   │   ├── mcp_service_decorator.py
│   │   ├── mcp_service_scanner.py
│   │   ├── extract_types.py
│   │   └── pydantic_to_schema.py
│   ├── static/                   # 웹에디터 프론트엔드
│   └── templates/                # 웹에디터 HTML
│
└── jinja/                        # 서버 생성 템플릿
    ├── generate_universal_server.py
    └── templates/
        ├── server_rest.py.jinja2
        ├── server_stdio.py.jinja2
        └── server_stream.py.jinja2
```

## 복사 명령어 예시

```bash
# 대상 프로젝트로 필수 폴더 복사
cp -r .claude/skills/mcp-setup TARGET_PROJECT/.claude/skills/
cp -r .claude/commands TARGET_PROJECT/.claude/
cp -r mcp_editor TARGET_PROJECT/
cp -r jinja TARGET_PROJECT/
```

## 폴더별 역할

| 폴더 | 역할 |
|------|------|
| `.claude/skills/mcp-setup/` | 스킬 정의 + 참조 템플릿 |
| `.claude/commands/` | 웹에디터/용어 가이드 문서 |
| `mcp_editor/` | 웹에디터 + 서비스 레지스트리 |
| `jinja/` | MCP 서버 코드 생성 템플릿 |
