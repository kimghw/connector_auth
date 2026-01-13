# 레지스트리 서버 데이터 흐름

## 요약

| 항목 | 내용 |
|------|------|
| **생성 스크립트** | `mcp_service_scanner.py` |
| **생성 함수** | `export_services_to_json(base_dir, server_name, output_dir)` |
| **출력 파일** | `registry_{server}.json` |
| **호출 시점** | 웹 에디터 시작 시 `scan_all_registries()` 자동 호출 |
| **API 엔드포인트** | `GET /api/mcp-services`, `GET /api/registry` |

### 참조 스크립트

| 스크립트 | 함수/메서드 | 용도 |
|----------|-------------|------|
| `service_registry.py` | `load_services_for_server()` | 서비스 메타데이터 로드 |
| `service_registry.py` | `scan_all_registries()` | 전체 프로필 스캔 |
| `registry_routes.py` | `get_mcp_services()` | API 응답 생성 |
| `registry_routes.py` | `get_registry()` | 레지스트리 파일 직접 반환 |
| `tool_loader.py` | `load_mcp_service_factors()` | 서비스 팩터 추출 |

### 지원 언어

| 언어 | 확장자 | 파서 | 데코레이터 |
|------|--------|------|-----------|
| Python | `.py` | `ast` (내장) | `@mcp_service` |
| JavaScript | `.js`, `.mjs` | `esprima` | `@McpService` |
| TypeScript | `.ts`, `.tsx` | `esprima` | `@McpService` |

**조건**: JavaScript/TypeScript 스캔 시 `pip install esprima` 필요

**주의사항**:
- `esprima` 미설치 시 → JS 파일 스킵 (경고만 출력)
- 순수 JavaScript는 데코레이터 문법 없음 → TypeScript 권장
- camelCase → snake_case 자동 변환 (`serverName` → `server_name`)

---

## registry_{server}.json 구조

```
{
  "version": "1.0",                       ← 레지스트리 포맷 버전
  "generated_at": "2026-01-13T...",       ← 생성 시간 (ISO datetime)
  "server_name": "outlook",               ← 서버 이름
  "services": {                           ← 서비스별 메타데이터
    "query_mail_list": {
      "service_name": "query_mail_list",
      "handler": {
        "class_name": "MailService",      ← 클래스명
        "instance": "mail_service",       ← 인스턴스 변수명 (snake_case)
        "method": "query_mail_list",      ← 호출할 메서드명
        "is_async": true,                 ← 비동기 함수 여부
        "file": "/path/to/service.py",    ← 소스 파일 절대 경로
        "line": 64                        ← 함수 정의 라인 번호
      },
      "signature": "user_email: str, filter_params: Optional[FilterParams] = None",
      "parameters": [
        {
          "name": "user_email",           ← 파라미터 이름
          "type": "str",                  ← JSON Schema 호환 타입
          "is_optional": false,           ← Optional 여부 (false = 필수)
          "default": null,                ← 기본값
          "has_default": false            ← 기본값 존재 여부
        },
        {
          "name": "filter_params",
          "type": "object",               ← 클래스 타입은 "object"
          "class_name": "FilterParams",   ← 원본 클래스 이름
          "is_optional": true,            ← Optional 여부 (true = 선택)
          "default": null,
          "has_default": true
        }
      ],
      "metadata": {
        "tool_name": "handler_mail_list", ← MCP 도구 이름
        "server_name": "outlook",         ← 서버 식별자
        "category": "outlook_mail",       ← 카테고리
        "tags": ["query", "search"],      ← 태그 목록
        "priority": 5,                    ← 우선순위
        "description": "메일 리스트 조회"  ← 기능 설명
      }
    }
  }
}
```

> **제거된 필드**:
> - `is_required`: `is_optional`의 반대이므로 중복
> - `module_path`: `file`에서 추출 가능하므로 중복

---

## API 엔드포인트

**파일**: `tool_editor_core/routes/registry_routes.py`

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/registry` | GET | 특정 프로필의 레지스트리 파일 조회 |
| `/api/mcp-services` | GET | MCP 서비스 목록 및 상세 정보 |

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
      "file": "/path/to/service.py"
    }
  ],
  "groups": {},
  "is_merged": false,
  "source_profiles": []
}
```

---

## 데이터 흐름

```
[빌드타임]

소스 코드 (@mcp_service 데코레이터)
         │
         ▼
웹에디터 시작
         │
         ▼
scan_all_registries()
         │
         ▼
mcp_service_scanner.py (AST 스캔)
         │
         ▼
registry_{server}.json 생성
         │
         ▼
GET /api/mcp-services
         │
         ▼
JSON 응답 → 웹 UI 표시
```

---

## type vs class_name 분리

### 배경
기존에는 `type` 필드에 클래스 이름이 직접 저장됨 (예: `"type": "FilterParams"`)
이는 JSON Schema 타입과 혼동되어 일관성 문제 발생

### 변경 후 구조

| 상황 | type | class_name |
|------|------|------------|
| 기본 타입 | `str`, `int`, `bool` | (없음) |
| 제네릭 타입 | `List[str]`, `Dict[str, Any]` | (없음) |
| 커스텀 클래스 | `object` | `FilterParams` |

### 판별 로직 (`mcp_service_scanner.py:_is_class_type`)

```python
def _is_class_type(type_str: str) -> bool:
    # PascalCase이고 제네릭 아닌 경우 = 클래스
    if not type_str[0].isupper():
        return False
    generic_prefixes = ("List[", "Dict[", "Union[", "Optional[", ...)
    if any(type_str.startswith(prefix) for prefix in generic_prefixes):
        return False
    return True
```

---

## 핵심 개념

### Handler vs Metadata

| 구분 | Handler | Metadata |
|------|---------|----------|
| 역할 | 실행 라우팅 정보 | 분류/설명 정보 |
| 예시 | class_name, method, file | category, tags, description |
| 사용 | 런타임 호출 | UI 표시, 검색 필터링 |
