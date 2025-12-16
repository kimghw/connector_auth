# MCP Server Generator

Jinja2 템플릿 기반 MCP 서버 자동 생성 도구

## 개요

이 도구는 MCP tool definitions에서 자동으로 FastAPI 서버를 생성합니다. Object 파라미터와 일반 파라미터를 구분하여 적절히 처리합니다.

## 주요 기능

- ✅ Tool definitions에서 서버 코드 자동 생성
- ✅ Object 파라미터를 클래스 인스턴스로 자동 변환
- ✅ 동적 import 및 서비스 객체 관리
- ✅ Python과 JSON 형식의 tool definitions 지원
- ✅ 커스텀 템플릿 지원
- ✅ `generate_server.py` 하나로 outlook/file_handler/scaffold 템플릿 자동 선택

## 사용법

### 기본 사용법 (Outlook)

```bash
python generate_server.py \
  --tools ../mcp_editor/outlook/tool_definition_templates.py \
  --server outlook \
  --output ../outlook_mcp/mcp_server/server_generated.py
```

### File Handler 템플릿 사용

```bash
python generate_server.py \
  --tools ../mcp_editor/file_handler/tool_definition_templates.py \
  --server file_handler \
  --output ../mcp_file_handler/mcp_server/server_generated.py
```

### 커스텀 템플릿 지정

```bash
python generate_server.py \
  --tools ../mcp_editor/tool_definition_templates.py \
  --template ./custom_template.jinja2 \
  --output ../outlook_mcp/mcp_server/server_custom.py
```

### JSON 입력 사용

```bash
python generate_server.py \
  --tools ./tool_definitions.json \
  --output ./generated_server.py
```

### 스캐폴드 템플릿 (mcp_server_scaffold_template.jinja2)

```bash
python generate_server.py \
  --template ./mcp_server_scaffold_template.jinja2 \
  --output ../mcp_new/mcp_server/server.py \
  --server new_server
```

## 파일 구조

```
jinja/
├── generate_server.py               # 통합 생성 스크립트 (웹 에디터와 공유)
├── generate_outlook_server.py       # 서비스 분석 로직 포함
├── generate_file_handler_server.py  # 파일 핸들러 전용 생성기
├── generate_editor_config.py        # editor_config.json 생성기
├── generate_server_mappings.py      # 서버 매핑 자동 생성
├── scaffold_generator.py            # 신규 MCP 서버 스캐폴드 생성
├── outlook_server_template.jinja2   # Outlook 서버 템플릿
├── file_handler_server_template.jinja2  # 파일 핸들러 서버 템플릿
├── mcp_server_scaffold_template.jinja2  # 신규 서버 기본 템플릿
├── run_generator.sh                 # 사용 예제 스크립트
└── README.md                       # 이 문서
```

## Tool Definition 형식

Tool definitions는 다음 정보를 포함해야 합니다:

```python
{
    "name": "query_emails",
    "description": "Query and filter emails",
    "inputSchema": {
        "type": "object",
        "properties": {
            "filter": {
                "type": "object",
                "baseModel": "FilterParams"  # Object 타입은 baseModel 지정
            },
            "user_email": {
                "type": "string"  # 일반 파라미터
            }
        }
    },
    "mcp_service": {  # 선택적: 서비스 메타데이터
        "name": "query_filter",  # 실제 메서드명
        "class": "GraphMailQuery"
    }
}
```

## 생성되는 코드 특징

1. **자동 import 관리**: 필요한 모든 클래스와 타입 자동 import
2. **서비스 객체 초기화**: 서비스 클래스 인스턴스 자동 생성
3. **파라미터 변환**: Object 타입을 적절한 클래스로 자동 변환
4. **에러 처리**: MCP 프로토콜 에러 응답 처리

## 요구사항

- Python 3.6+
- Jinja2
- FastAPI (생성된 서버 실행용)

## 설치

```bash
pip install jinja2 fastapi
```

## 문제 해결

- **Import 오류**: tool definitions 파일의 경로가 올바른지 확인
- **템플릿 오류**: 템플릿 파일이 존재하고 문법이 올바른지 확인
- **생성 실패**: tool definitions의 형식이 올바른지 확인
