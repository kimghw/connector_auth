# mcp_outlook 디렉토리 구조 및 파일 설명

이 디렉토리는 MCP Outlook 서버의 웹 에디터 관련 파일들을 포함합니다.

## 📁 파일 목록 및 설명

### 1. **tool_definition_templates.py**
- **타입**: 🔄 자동 생성 (웹 에디터에서 Save 시)
- **용도**: 웹 에디터용 툴 정의 (메타데이터 포함 버전)
- **내용**: MCP_TOOLS 배열 + mcp_service 메타데이터
- **수정 방법**: 웹 에디터에서 편집 후 Save
- **주의**: 직접 편집하지 마세요. 웹 에디터로 수정하세요.

### 2. **tool_internal_args.json**
- **타입**: 🔄 자동 생성 (웹 에디터에서 Save 시)
- **용도**: 툴의 내부 파라미터 정의 저장
- **내용**: 각 툴의 내부 인자와 기본값
- **수정 방법**: 웹 에디터의 "Internal Args" 섹션에서 편집
- **형식**:
  ```json
  {
    "tool_name": {
      "param_name": {
        "type": "str",
        "default": "default_value"
      }
    }
  }
  ```

### 3. **outlook_mcp_services.json**
- **타입**: ❌ 현재 사용 안 됨 (레거시)
- **용도**: 이전 버전의 MCP 서비스 정보
- **참고**: 현재는 `mcp_service_registry/registry_outlook.json` 사용

### 4. **outlook_mcp_services_detailed.json**
- **타입**: ❌ 현재 사용 안 됨 (예비)
- **용도**: 상세 서비스 메타데이터 (향후 기능용)
- **내용**: 파일 위치, 라인 번호 등 디버깅 정보 포함

### 5. **backups/** 디렉토리
- **타입**: 🔄 자동 생성
- **용도**: 툴 정의 백업 파일 저장
- **파일명 형식**: `tool_definitions_YYYYMMDD_HHMMSS.py`
- **관리**: 최근 10개만 유지 (자동 삭제)
- **복원 방법**: 웹 에디터의 "Load Template" 드롭다운에서 선택

## 🔄 데이터 플로우

```
웹 에디터 시작
    ↓
tool_definition_templates.py 로드
    ↓
사용자 편집
    ↓
Save 버튼 클릭
    ↓
3개 파일 업데이트:
  - tool_definition_templates.py (여기)
  - tool_internal_args.json (여기)
  - ../mcp_outlook/mcp_server/tool_definitions.py (서버용)
```

## ⚠️ 중요 사항

1. **직접 편집 금지**: 모든 파일은 웹 에디터를 통해 수정하세요
2. **백업 자동 생성**: Save 시 자동으로 백업 생성됨
3. **동기화 유지**: tool_definition_templates.py와 tool_definitions.py는 항상 동기화됨

## 🚀 웹 에디터 실행

```bash
cd /home/kimghw/Connector_auth/mcp_editor
python tool_editor_web.py
```

브라우저에서 http://localhost:8091 접속

## 📝 파일 생성/업데이트 시점

| 파일 | 생성 시점 | 업데이트 시점 |
|------|----------|---------------|
| tool_definition_templates.py | 웹 에디터 첫 Save | 매 Save 시 |
| tool_internal_args.json | 내부 인자 첫 설정 | 내부 인자 변경 시 |
| backups/*.py | 매 Save 시 | - |

## 🔧 문제 해결

### Q: 파일이 동기화되지 않음
A: 웹 에디터에서 Reload 버튼 클릭 후 다시 Save

### Q: 백업 파일이 너무 많음
A: 10개 이상 시 자동 삭제됨. 수동 삭제도 가능

### Q: 메타데이터가 사라짐
A: tool_definition_templates.py가 아닌 tool_definitions.py를 편집한 경우. 웹 에디터 사용 필수

## 📚 관련 파일

- **서버 툴 정의**: `/mcp_outlook/mcp_server/tool_definitions.py`
- **레지스트리**: `/mcp_editor/mcp_service_registry/registry_outlook.json`
- **에디터 설정**: `/mcp_editor/editor_config.json`