---
name: setup_claude_desktop_outlook
description: Windows venv 생성 + 의존성 설치 + Claude Desktop에 Outlook MCP 서버 배포. Python 가상환경 설정, pip 의존성 설치, Claude Desktop config 병합을 자동으로 수행합니다. Outlook MCP 서버를 Claude Desktop에 연결할 때 사용합니다.
---

# Claude Desktop Outlook MCP 서버 설정

Windows에서 Outlook STDIO MCP 서버를 Claude Desktop으로 실행할 수 있도록 환경을 자동 설정합니다.

## 스킬 구성 파일

```
setup_claude_desktop.outlook/
├── SKILL.md                                          ← 실행 지침 (이 파일)
├── reference.md                                      ← 환경 요구사항, 경로 매핑, 의존성 정보
├── templates/
│   └── claude_desktop_config.template.json            ← Claude Desktop config 템플릿
└── scripts/
    └── verify_install.py                              ← 설치 검증 스크립트
```

- **reference.md**: 실행 전 환경 요구사항, WSL↔Windows 경로 매핑, 핵심 의존성, 병합 규칙 참조
- **templates/claude_desktop_config.template.json**: mcpServers 병합에 사용할 config 템플릿
- **scripts/verify_install.py**: 6단계 검증 시 venv python으로 실행

## 참조 Config

프로젝트의 `claude_desktop_config.json`을 소스로 사용합니다.
템플릿 참조: `templates/claude_desktop_config.template.json`

> 소스 파일의 `mcpServers` 항목이 Claude Desktop config에 병합됩니다.
> 새 MCP 서버가 추가되면 프로젝트 루트의 `claude_desktop_config.json`을 먼저 수정한 뒤 이 스킬을 재실행하면 됩니다.

---

## Instructions

> 실행 전 `reference.md`를 읽고 환경 요구사항과 경로 매핑을 확인하세요.

아래 단계를 **순서대로 모두 자동 실행**하세요. 각 단계의 명령을 Bash 도구로 직접 실행합니다.

### 1단계: Windows 시스템 Python 탐색

```bash
ls /mnt/c/Python3*/python.exe 2>/dev/null
```

- 여러 버전이 발견되면 사용자에게 선택하도록 질문
- 못 찾으면 사용자에게 Python 설치 경로를 질문

발견된 Python 경로를 `SYSTEM_PYTHON`으로 기억합니다.

**에러 처리:**
- Python을 찾지 못한 경우 → 사용자에게 경로를 직접 입력받고, 해당 경로가 존재하는지 `ls`로 확인
- 사용자가 제공한 경로도 존재하지 않으면 → **중단**, "Windows에 Python을 먼저 설치해주세요" 안내

### 2단계: venv 생성 (없으면)

```bash
ls /mnt/c/connector_auth/venv/Scripts/python.exe 2>/dev/null
```

- 이미 존재하면 "venv 존재, 의존성 업데이트만 수행" 출력 후 3단계로
- 없으면 생성:

```bash
$SYSTEM_PYTHON -m venv /mnt/c/connector_auth/venv
```

**에러 처리:**
- venv 생성 실패 (exit code ≠ 0) → 에러 메시지 출력, **중단**
- 생성 후 `venv/Scripts/python.exe` 존재 여부 재확인 → 없으면 **중단**

### 3단계: 의존성 설치

```bash
/mnt/c/connector_auth/venv/Scripts/pip.exe install -r /mnt/c/connector_auth/requirements.txt
```

- 타임아웃 300초

**에러 처리:**
- `requirements.txt`가 없는 경우 → **중단**, 파일 경로 확인 요청
- pip install 실패 (exit code ≠ 0) → 실패한 패키지명과 에러 메시지를 사용자에게 보여주고, 계속 진행할지 질문
- 타임아웃 초과 → "네트워크 상태를 확인하세요" 안내 후 **중단**

### 4단계: Claude Desktop config 위치 탐색

```bash
ls /mnt/c/Users/*/AppData/Roaming/Claude/claude_desktop_config.json 2>/dev/null
```

- 발견된 경로를 `CLAUDE_CONFIG`로 기억
- 못 찾으면 사용자에게 경로를 질문
- 여러 사용자 프로필이 발견되면 사용자에게 선택하도록 질문

**에러 처리:**
- config 파일을 찾지 못하고, 사용자도 경로를 모르는 경우 → Claude Desktop이 설치되어 있는지 확인 안내, **중단**
- config 파일이 유효한 JSON이 아닌 경우 → 파일 내용 출력 후 "config 파일이 손상되었습니다" 안내, **중단**

### 5단계: Claude Desktop config 병합

1. **소스 파일 읽기**: `/mnt/c/connector_auth/claude_desktop_config.json` (Read 도구 사용)
2. **대상 파일 읽기**: `$CLAUDE_CONFIG` (Read 도구 사용)
3. **병합 규칙**:
   - 소스의 `mcpServers` 각 항목을 대상의 `mcpServers`에 **upsert** (같은 키면 덮어쓰기, 없으면 추가)
   - 대상의 `preferences`, 기타 최상위 키는 **그대로 유지**
   - 소스에만 있는 최상위 키(`mcpServers` 외)는 무시
4. 병합 결과를 사용자에게 보여주고 **확인받은 후** Write 도구로 저장

**에러 처리:**
- 소스 파일에 `mcpServers` 키가 없는 경우 → "소스 config에 mcpServers가 없습니다" 안내, **중단**
- 대상 파일 쓰기 실패 (권한 등) → 에러 메시지 출력, 수동 적용할 JSON을 출력해주고 **중단**
- 사용자가 병합 결과를 거부한 경우 → 파일 수정 없이 **중단**

### 6단계: 검증

`scripts/verify_install.py`를 venv python으로 실행합니다:

```bash
/mnt/c/connector_auth/venv/Scripts/python.exe \
    /mnt/c/connector_auth/.claude/skills/setup_claude_desktop.outlook/scripts/verify_install.py
```

또는 개별 검증:

```bash
# venv Python 버전 확인
/mnt/c/connector_auth/venv/Scripts/python.exe -c "import sys; print(sys.version)"

# 핵심 패키지 import 테스트
/mnt/c/connector_auth/venv/Scripts/python.exe -c "import aiohttp, pydantic, yaml, dotenv; print('All core imports OK')"
```

**에러 처리:**
- import 실패 → 실패한 패키지명 출력, `pip install <패키지>` 재시도 1회, 여전히 실패 시 사용자에게 안내
- verify_install.py 실행 자체 실패 → 개별 검증 명령으로 폴백

검증 성공 시 최종 요약 출력:
- venv 경로
- 설치된 패키지 수
- Claude Desktop config 적용 결과
- "Claude Desktop을 재시작하면 Outlook MCP 서버가 활성화됩니다"

---

## Examples

입력: `/setup_claude_desktop_outlook`
출력:
```
1. Windows Python 발견: C:\Python312\python.exe
2. venv 존재 확인 → 의존성 업데이트
3. pip install 완료 (32개 패키지)
4. Claude Desktop config 발견: C:\Users\kimghw\AppData\Roaming\Claude\claude_desktop_config.json
5. mcpServers.outlook 항목 병합 완료
6. 검증 통과 — Claude Desktop을 재시작하면 Outlook MCP 서버가 활성화됩니다
```

---

## 주의사항

- venv가 이미 존재하면 재생성하지 않고 `pip install`만 재실행
- Claude Desktop config의 `preferences` 등 기존 설정은 절대 삭제하지 않음
- Claude Desktop 재시작 필요 안내
- WSL에서 Windows 바이너리(`/mnt/c/...`)를 직접 호출
