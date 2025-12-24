---
description: "MCP 서비스 Facade 패턴 구현 및 서버 설정 자동화"
---

# MCP Service Setup - Facade 패턴 및 MCP 통합

이 스킬은 새로운 프로젝트에 MCP 서버 구조를 설정하고, Facade 패턴을 적용하여 서비스를 구성하는 작업을 자동화합니다.

## 작업 방식

이 스킬은 다음과 같은 방식으로 작동합니다:

1. **프로젝트 정보 수집**: 프로젝트명과 서비스 주제를 입력받습니다
2. **디렉토리 구조 생성**: `mcp_{project_name}` 폴더와 하위 구조를 생성합니다
3. **Facade 서비스 구현**: `{subject}_service.py` 파일을 생성하고 `@mcp_service` 데코레이터를 적용합니다
4. **웹에디터 연동**: 웹에디터의 템플릿과 generate_server 기능을 활용하여 서버 파일을 자동 생성합니다
5. **레지스트리 등록**: 웹에디터가 자동으로 서비스를 스캔하고 등록합니다

## 주요 작업 내용

### 1. 프로젝트 구조 생성
- `mcp_{project_name}/` 디렉토리 생성
- `mcp_{project_name}/{subject}_service.py` Facade 레이어 생성
- `mcp_{project_name}/mcp_server/` 폴더 구조 생성

### 2. 웹에디터 템플릿 설정
- `mcp_editor/mcp_{project_name}/` 디렉토리 생성
- `tool_definition_templates.py` 기본 도구 정의 파일 생성
- 초기 도구 템플릿 포함

### 3. editor_config.json 업데이트
- 웹에디터 설정 템플릿 사용
- 새 프로젝트를 설정에 추가
- 서비스 경로 및 메타데이터 등록

### 4. Facade 서비스 구현
- 핵심 클래스를 감싸는 `{subject}_service.py` 생성
- `@mcp_service` 데코레이터 각 메서드에 적용
- 외부 노출용 인터페이스만 선별하여 제공

### 5. 서버 파일 생성
- 웹에디터의 generate_server 기능 활용
- 템플릿 기반 `server.py` 자동 생성
- `tool_definitions.py` 및 기타 필요 파일 생성

## 실행 단계

1. **프로젝트 정보 수집**
   - 프로젝트 이름 입력 (예: outlook, file_handler)
   - 서비스 주제 입력 (예: mail, file, db)
   - 핵심 클래스 식별

2. **디렉토리 구조 생성**
   ```
   mcp_{project_name}/
   ├── {subject}_service.py
   └── mcp_server/

   mcp_editor/
   └── mcp_{project_name}/
       └── tool_definition_templates.py

   .claude/
   ├── commands/
   │   └── {project_name}_helper.md  # 프로젝트별 헬퍼 커맨드
   └── agents/
       └── {project_name}.yaml        # 프로젝트별 에이전트 설정
   ```

3. **Jinja 템플릿 활용**
   - `jinja/universal_server_template.jinja2` 사용하여 server.py 생성
   - `jinja/editor_config_template.jinja2` 사용하여 editor_config.json 생성
   - `jinja/generate_universal_server.py` 실행하여 서버 생성

4. **editor_config.json 생성/업데이트**
   - `jinja/generate_editor_config.py` 실행
   - 웹에디터 템플릿 활용
   - 프로젝트 경로 설정
   - 서비스 메타데이터 등록

5. **Facade 서비스 구현**
   - `{subject}_service.py` 파일 생성
   - `@mcp_service` 데코레이터 적용
   - 노출할 메서드 선별 및 구현

6. **도구 템플릿 생성**
   - `tool_definition_templates.py` 작성
   - 기본 MCP_TOOLS 정의 포함
   - 초기 도구 설정 제공

7. **Claude 커맨드 및 에이전트 생성**
   - `.claude/commands/{project_name}_helper.md` 생성
   - 프로젝트별 헬퍼 명령어 정의
   - `.claude/agents/{project_name}.yaml` 에이전트 설정

8. **서버 생성 및 배포**
   - `jinja/generate_universal_server.py` 실행
   - `jinja/scaffold_generator.py` 로 프로젝트 스캐폴딩
   - 템플릿 기반 `server.py` 생성
   - `@mcp_service` 스캔 및 등록

9. **레지스트리 자동 등록**
   - 웹에디터가 `registry_{project_name}.json` 생성
   - 도구들이 웹 인터페이스에 표시
   - `jinja/generate_server_mappings.py`로 매핑 생성

## 단계별 체크포인트
1. **입력 확정**: `project_name`/`subject`/`core_class`가 컨벤션을 따르는지, 동일 이름의 기존 프로필이 없는지 확인 (충돌 시 경로 덮어쓰기 주의).
2. **스캐폴딩 확인**: `mcp_{project_name}/`와 `mcp_editor/mcp_{project_name}/`가 생성됐는지, `{subject}_service.py`/`tool_definition_templates.py`가 비어 있지 않은지 확인.
3. **Facade 구현 점검**: 노출할 메서드에 `@mcp_service`가 모두 적용됐는지, `server_name`/`profile_key` 일관성이 있는지, core_class 주입·예외 처리 기본값이 있는지 확인.
4. **도구-서비스 매핑**: `MCP_TOOLS` 이름이 Facade 메서드와 매칭되는지, `tool_names` 메타데이터와 registry 항목이 일치하는지, 필요한 `tool_internal_args.json`가 있으면 위치가 맞는지 확인.
5. **템플릿 실행 결과**: `python jinja/generate_universal_server.py {server_name}` 실행 후 `mcp_{project_name}/mcp_server/server.py`가 갱신됐는지, `python jinja/generate_editor_config.py` 실행 후 `mcp_editor/editor_config.json`에 새 프로필이 추가됐는지(백업 파일 생성됨) 확인.
6. **Claude 연동 파일**: `.claude/commands/{project_name}_helper.md`와 `.claude/agents/{project_name}.yaml`에 새 프로젝트가 반영됐는지, 네이밍 규칙을 지키는지 확인.
7. **최종 스모크**: `mcp_editor/registry_{project_name}.json`에 도구가 노출되는지, 웹 에디터/CLI에서 도구 호출 시 Facade 메서드가 실제로 실행되는지 빠르게 검증.

## 자동 생성 파일

### MCP 프로젝트 파일
- `mcp_{project_name}/{subject}_service.py` - Facade 구현
- `mcp_{project_name}/mcp_server/server.py` - MCP 서버 (Jinja 템플릿 생성)
- `mcp_{project_name}/mcp_server/tool_definitions.py` - 도구 정의

### 웹에디터 파일
- `mcp_editor/mcp_{project_name}/tool_definition_templates.py` - 도구 템플릿
- `mcp_editor/registry_{project_name}.json` - 서비스 레지스트리
- `mcp_editor/editor_config.json` - 에디터 설정 (업데이트)

### Claude 파일
- `.claude/commands/{project_name}_helper.md` - 프로젝트 헬퍼 커맨드
- `.claude/agents/{project_name}.yaml` - 프로젝트 에이전트 설정

### Jinja 템플릿 활용
- `jinja/universal_server_template.jinja2` - 서버 템플릿
- `jinja/editor_config_template.jinja2` - 에디터 설정 템플릿
- `jinja/mcp_server_scaffold_template.jinja2` - 스캐폴드 템플릿

## 네이밍 컨벤션 (필수 준수)

프로젝트 생성 시 반드시 다음 네이밍 규칙을 따라야 합니다:

### 디렉토리 및 파일명
| 항목 | 규칙 | 예시 |
|------|------|------|
| 프로젝트 디렉토리 | `mcp_{project_name}/` | `mcp_outlook/`, `mcp_file_handler/` |
| 서비스 파일 | `{subject}_service.py` | `mail_service.py`, `file_service.py` |
| 에디터 프로필 | `mcp_editor/mcp_{project_name}/` | `mcp_editor/mcp_outlook/` |
| 레지스트리 | `registry_{project_name}.json` | `registry_outlook.json` |

### 코드 네이밍
| 항목 | 규칙 | 예시 |
|------|------|------|
| server_name | lowercase, 언더스코어 허용 | "outlook", "file_handler" |
| profile_key | `mcp_{server_name}` 형식 | "mcp_outlook" |
| 메서드명 | snake_case, 동사로 시작 | "fetch_mail", "send_message" |
| 클래스명 | PascalCase, 명사형 | "MailService", "FileHandler" |
| 인스턴스명 | snake_case | "mail_service", "file_handler" |
| tool_name | snake_case 또는 lowercase | "mail_fetch", "file_upload" |

### 주기적 검토 체크리스트
1. **네이밍 일관성**: 모든 파일과 변수명이 컨벤션을 따르는지 확인
2. **경로 구조**: `mcp_{project_name}` 형식 유지 확인
3. **레지스트리 동기화**: `registry_{project_name}.json` 정확성 확인
4. **템플릿 호환성**: Jinja 템플릿과 네이밍 일치 확인
5. **Claude 명령어**: `.claude/commands/` 파일명 일관성 확인

## 입력 파라미터
- **project_name**: 프로젝트 이름 (예: outlook, database, file_handler) - lowercase, 언더스코어 허용
- **subject**: 서비스 주제 (예: mail, db, file) - lowercase
- **core_class**: 핵심 클래스명 (예: GraphMailClient, DatabaseClient) - PascalCase
- **methods**: 노출할 메서드 목록 (선택적) - snake_case

작업을 시작하려면 프로젝트 이름과 서비스 주제를 알려주세요. 네이밍 컨벤션은 자동으로 적용됩니다.
