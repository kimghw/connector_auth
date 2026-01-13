# 레지스트리 서버 데이터 흐름

## 파일 구조

```
mcp_editor/
├── mcp_service_registry/              # 레지스트리 핵심 모듈
│   ├── meta_registry.py               # 레지스트리 매니저 클래스
│   ├── mcp_service_scanner.py         # AST 기반 코드 스캐너
│   ├── mcp_service_decorator.py       # @mcp_service 데코레이터
│   ├── extract_types.py               # 타입 정보 추출
│   ├── registry_outlook.json          # Outlook 서비스 레지스트리
│   ├── registry_calendar.json         # Calendar 서비스 레지스트리
│   └── registry_file_handler.json     # File Handler 서비스 레지스트리
│
├── tool_editor_core/
│   ├── service_registry.py            # 서비스 로딩/스캔 함수
│   ├── config.py                      # 경로 및 설정 관리
│   └── routes/
│       └── registry_routes.py         # 레지스트리 API 엔드포인트
```

---

## registry_{server}.json 구조

```json
{
  "version": "1.0",
  "generated_at": "2026-01-12T20:33:22.863075",
  "server_name": "outlook",
  "services": {
    "query_mail_list": {
      "service_name": "query_mail_list",
      "handler": {
        "class_name": "MailService",
        "module_path": "mcp_outlook.outlook_service",
        "instance": "mail_service",
        "method": "query_mail_list",
        "is_async": true,
        "file": "/path/to/outlook_service.py",
        "line": 64
      },
      "signature": "user_email: str, query_method: Optional[QueryMethod] = ...",
      "parameters": [
        {
          "name": "user_email",
          "type": "str",
          "is_optional": false,
          "is_required": true,
          "default": null,
          "has_default": false
        }
      ],
      "metadata": {
        "tool_name": "handler_mail_list",
        "server_name": "outlook",
        "category": "outlook_mail",
        "tags": ["query", "search"],
        "priority": 5,
        "description": "메일 리스트 조회 기능"
      }
    }
  },
  "sources": ["static_scanner"],
  "statistics": {
    "total_services": 12,
    "runtime_services": 0,
    "static_services": 12
  }
}
```

### 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `version` | str | 레지스트리 포맷 버전 |
| `generated_at` | ISO datetime | 생성 시간 |
| `server_name` | str | 서버 이름 |
| `services` | dict | 서비스별 메타데이터 |
| `sources` | list | 데이터 수집 소스 |
| `statistics` | object | 통계 정보 |

### handler 필드

| 필드 | 설명 |
|------|------|
| `class_name` | 클래스명 (MailService) |
| `module_path` | Python import 경로 |
| `instance` | 인스턴스 변수명 |
| `method` | 호출할 메서드명 |
| `is_async` | 비동기 함수 여부 |
| `file` | 소스 파일 절대 경로 |
| `line` | 함수 정의 라인 번호 |

---

## MetaRegisterManager 클래스

**파일**: `mcp_service_registry/meta_registry.py`

### 주요 메서드

| 메서드 | 설명 |
|--------|------|
| `register_service(service_name, metadata)` | 서비스 등록 |
| `unregister_service(service_name)` | 서비스 해제 |
| `get_service_metadata(service_name)` | 서비스 메타데이터 조회 |
| `list_registered_services()` | 등록된 서비스 목록 |
| `get_registry_snapshot()` | 레지스트리 스냅샷 |

### 파일 I/O

| 메서드 | 설명 |
|--------|------|
| `export_registry(file_path)` | 레지스트리 파일 내보내기 |
| `import_registry(file_path)` | 레지스트리 파일 가져오기 |

### 데이터 수집

| 메서드 | 설명 |
|--------|------|
| `collect_from_decorator()` | 런타임 데코레이터에서 수집 |
| `collect_from_scanner(base_dir, server_name)` | 정적 스캐너에서 수집 |

### 매니페스트 생성

| 메서드 | 설명 |
|--------|------|
| `generate_service_manifest(base_dir, server_name, include_runtime, include_static)` | 서비스 매니페스트 생성 |
| `export_service_manifest(file_path, base_dir, server_name)` | 매니페스트 파일 내보내기 |

---

## service_registry.py 함수

**파일**: `tool_editor_core/service_registry.py`

| 함수 | 설명 |
|------|------|
| `load_services_for_server(server_name, scan_dir, force_rescan)` | 서비스 메타데이터 로드 |
| `scan_all_registries()` | 모든 프로필 레지스트리 스캔 |

### 캐싱 메커니즘
```python
SERVICE_SCAN_CACHE: dict[tuple[str, str], dict] = {}
# 키: (server_name, scan_dir)
# 값: 추출된 서비스 메타데이터
```

### load_services_for_server 흐름
```
1. registry_{server_name}.json 확인
2. 파일 존재 → JSON 로드 후 반환 (빠름)
3. force_rescan=True or 파일 없음 → AST 스캔 실행
4. 캐싱: SERVICE_SCAN_CACHE에 저장
```

---

## API 엔드포인트

**파일**: `tool_editor_core/routes/registry_routes.py`

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/registry` | GET | 특정 프로필의 레지스트리 파일 조회 |
| `/api/mcp-services` | GET | MCP 서비스 목록 및 상세 정보 |
| `/api/template-sources` | GET | 사용 가능한 템플릿 파일 목록 |
| `/api/template-sources/load` | POST | 템플릿 파일에서 MCP_TOOLS 로드 |

### GET /api/mcp-services 응답
```json
{
  "services": ["service1", "service2"],
  "services_with_signatures": [
    {
      "name": "service1",
      "parameters": [...],
      "signature": "param1: str, ...",
      "class_name": "ClassName",
      "module_path": "module.path"
    }
  ],
  "groups": {},
  "is_merged": false,
  "source_profiles": []
}
```

---

## 쓰기 흐름 (Write Flow)

```
1단계: 소스 코드 작성
─────────────────────
mcp_outlook/outlook_service.py
  └── @mcp_service 데코레이터가 붙은 함수들


2단계: 데코레이터 런타임 등록 (옵션)
──────────────────────────────────
@mcp_service(
    tool_name="mail_list_query",
    description="메일 리스트 조회",
    server_name="outlook"
)
async def query_mail_list(...):
    pass

  → MCP_SERVICE_REGISTRY 글로벌 변수에 등록


3단계: 스캔 (빌드타임)
─────────────────────
scan_all_registries() 호출
  └── mcp_service_scanner.py
       ├── AST 파싱하여 @mcp_service 찾기
       ├── 함수 시그니처 추출
       └── MetaRegisterManager로 전달


4단계: 매니페스트 생성
─────────────────────
MetaRegisterManager.generate_service_manifest()
  ├── collect_from_decorator()  (런타임)
  ├── collect_from_scanner()    (정적)
  └── 중복 제거: runtime > static


5단계: 파일 내보내기
─────────────────────
registry_{server}.json 파일 생성
```

---

## 읽기 흐름 (Read Flow)

```
1단계: 웹에디터 시작
─────────────────────
tool_editor_web.py 시작
  └── scan_all_registries() 자동 호출


2단계: 프로필별 레지스트리 로드
──────────────────────────────
load_services_for_server(server_name, scan_dir, force_rescan=False)

  조건 분기:
  ├── force_rescan=False && JSON 존재 → JSON 로드 (빠름)
  └── force_rescan=True or 없음 → AST 스캔 (느림)


3단계: 캐싱
─────────────────────
SERVICE_SCAN_CACHE[(server_name, scan_dir)] = services


4단계: API 응답
─────────────────────
GET /api/mcp-services?profile=outlook
  └── registry_routes.py:get_mcp_services()
       ├── registry_outlook.json 로드
       └── services dict → decorated list 변환
```

---

## 조회 흐름 (Query Flow)

```
1단계: 웹 UI에서 프로필 선택
──────────────────────────────
사용자가 드롭다운에서 "outlook" 선택


2단계: API 호출
──────────────────────────────
GET /api/mcp-services?profile=outlook


3단계: registry 경로 결정
──────────────────────────────
get_mcp_services():
  └── 우선순위 경로 검색:
       1. mcp_service_registry/registry_{server}.json (신규)
       2. mcp_{server}/{registry_name}_mcp_services.json (구형)
       3. {registry_name}_mcp_services.json (레거시)


4단계: 데이터 변환
──────────────────────────────
registry.json → services dict → UI용 list


5단계: 응답 반환
──────────────────────────────
{ "services": [...], "services_with_signatures": [...] }
```

---

## 현재 레지스트리 현황

### Outlook 서버 (registry_outlook.json)
- 서비스 수: 12개
- 클래스: MailService
- 모듈: mcp_outlook.outlook_service
- 주요 서비스: query_mail_list, fetch_and_process, download_attachments 등

### Calendar 서버 (registry_calendar.json)
- 서비스 수: 7개
- 클래스: CalendarService
- 모듈: calendar.calendar_service
- 주요 서비스: list_events, create_event, update_event, delete_event 등

### File Handler 서버 (registry_file_handler.json)
- 서비스 수: 7개
- 클래스: FileManager
- 모듈: file_handler.file_manager
- 주요 서비스: process, process_directory, save_metadata 등

---

## 핵심 개념

### Handler vs Metadata

| 구분 | Handler | Metadata |
|------|---------|----------|
| 역할 | 실행 라우팅 정보 | 분류/설명 정보 |
| 예시 | class_name, method, instance | category, tags, description |
| 사용 | 코드 생성, 런타임 호출 | UI 표시, 검색 필터링 |

### 데이터 4계층 구조

```
┌─────────────────────┐
│ 소스 코드           │  @mcp_service 데코레이터
├─────────────────────┤
│ 레지스트리 (JSON)   │  registry_{server}.json
├─────────────────────┤
│ 웹 API              │  /api/mcp-services
├─────────────────────┤
│ 런타임 실행         │  handler 함수 호출
└─────────────────────┘
```

---

## 전체 흐름도

```
[빌드타임]

소스 코드 (@mcp_service)
         │
         ▼
웹에디터 시작 / Reload
         │
         ▼
scan_all_registries()
         │
         ▼
mcp_service_scanner.py (AST 스캔)
         │
         ▼
MetaRegisterManager.generate_service_manifest()
         │
         ▼
registry_{server}.json 생성/갱신
         │
         ▼
웹 UI 로드
         │
         ▼
GET /api/mcp-services
         │
         ▼
registry_routes.py:get_mcp_services()
         │
         ▼
JSON 응답


[런타임]

LLM 요청 수신
         │
         ▼
handler_{tool_name}(args)
         │
         ▼
registry 정보 참조
         │
         ▼
실제 서비스 메서드 호출
         │
         ▼
결과 반환
```
