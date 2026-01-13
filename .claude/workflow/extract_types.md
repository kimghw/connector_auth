# 타입 추출 시스템

## 요약

| 항목 | 내용 |
|------|------|
| **모듈** | `mcp_service_registry/extract_types.py` |
| **호출자** | `mcp_service_scanner.py` |
| **출력 파일** | `types_property_{server}.json` |
| **호출 시점** | 웹 에디터 시작 시 자동 실행 |

### 참조 스크립트

| 스크립트 | 함수 | 용도 |
|----------|------|------|
| `mcp_service_scanner.py` | `collect_referenced_types()` | 서비스 파라미터에서 클래스 타입 수집 |
| `mcp_service_scanner.py` | `resolve_class_file()` | import 추적하여 클래스 정의 파일 찾기 |
| `mcp_service_scanner.py` | `export_types_property()` | types_property JSON 생성 |
| `extract_types.py` | `extract_class_properties()` | 클래스별 프로퍼티 추출 |
| `extract_types.py` | `extract_single_class()` | 특정 클래스만 추출 |
| `basemodel_routes.py` | `GET /api/graph-types-properties` | API로 타입 정보 제공 |

---

## 동작 흐름

```
[웹 에디터 시작]
app.py:run_app()
         │
         ▼
service_registry.py:scan_all_registries()
         │
         ▼
mcp_service_scanner.py:export_services_to_json()
         │
         ├─→ registry_{server}.json 생성
         │
         └─→ 파라미터에서 type:"object" + class_name 발견
                      │
                      ▼
              resolve_class_file() ← import 추적
                      │
                      ▼
              extract_types.extract_single_class() ← 프로퍼티 추출
                      │
                      ▼
              types_property_{server}.json 생성
```

---

## 핵심 개념

### Import 추적

서비스 함수의 파라미터가 `type: "object"` + `class_name`인 경우:

1. 해당 서비스 파일의 import 문 분석
2. class_name이 어느 모듈에서 왔는지 확인
3. 모듈 경로를 실제 파일 경로로 변환
4. 해당 파일에서 클래스 프로퍼티 추출

```python
# service.py
from outlook_types import FilterParams  ← import 추적

def query_mail_list(filter_params: FilterParams):  ← class_name 발견
    ...

# → outlook_types.py에서 FilterParams 프로퍼티 추출
```

---

## 출력 파일 구조

**파일**: `types_property_{server}.json`

```
{
  "version": "1.0",
  "generated_at": "2026-01-13T...",
  "server_name": "outlook",
  "classes": [                           ← 추출된 클래스 목록
    {
      "name": "FilterParams",
      "file": "/path/to/outlook_types.py",  ← 클래스 정의 파일
      "line": 15,                           ← 정의 라인 번호
      "property_count": 3
    }
  ],
  "properties_by_class": {               ← 클래스별 프로퍼티 그룹
    "FilterParams": [
      {
        "name": "user_email",
        "type": "string",
        "description": "사용자 이메일",
        "examples": [],
        "default": null
      }
    ]
  },
  "all_properties": [                    ← 전체 프로퍼티 평탄화 목록
    {
      "name": "user_email",
      "type": "string",
      "description": "사용자 이메일",
      "class": "FilterParams",
      "full_path": "FilterParams.user_email"
    }
  ]
}
```

---

## 주요 함수

### mcp_service_scanner.py

| 함수 | 설명 |
|------|------|
| `_parse_imports()` | 파일의 import 문 파싱 |
| `_resolve_module_to_file()` | 모듈명 → 파일 경로 변환 |
| `resolve_class_file()` | 클래스가 정의된 파일 찾기 |
| `collect_referenced_types()` | 모든 서비스에서 참조된 타입 수집 |
| `export_types_property()` | JSON 파일 생성 |

### extract_types.py

| 함수 | 설명 |
|------|------|
| `extract_class_properties()` | 파일 내 모든 BaseModel 클래스 추출 |
| `extract_single_class()` | 특정 클래스만 추출 |
| `extract_field_info()` | Field() 정의에서 메타데이터 추출 |
| `map_python_to_json_type()` | Python 타입 → JSON Schema 타입 |

---

## 타입 매핑

| Python 타입 | JSON Schema 타입 |
|-------------|------------------|
| `str` | `string` |
| `int` | `integer` |
| `float` | `number` |
| `bool` | `boolean` |
| `list`, `List[T]` | `array` |
| `dict`, `Dict[K,V]` | `object` |
| `Optional[T]` | T의 타입 |
| 커스텀 클래스 | `object` |

---

## API 엔드포인트

**`GET /api/graph-types-properties`**

types_property_{server}.json 파일을 읽어서 반환.
파일은 웹 에디터 시작 시 자동 생성됨.

---

## 연관 파일

- `registry_{server}.json` - 서비스 정의 (파라미터에 class_name 포함)
- `types_property_{server}.json` - 참조된 타입 프로퍼티 정보
- `profile_management.py` - 프로필 삭제 시 두 파일 모두 제거
