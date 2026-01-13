# 타입 추출 시스템

## 요약

| 항목 | 내용 |
|------|------|
| **모듈** | `mcp_service_registry/extract_types.py` |
| **호출자** | `mcp_service_scanner.py` |
| **출력 파일** | `types_property_{server}.json` |
| **호출 시점** | 웹 에디터 시작 시 자동 실행 |
| **설정 의존** | 없음 (import 자동 추적) |

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

## 핵심 특징

### 자동 클래스 추적

**설정 파일(types_files) 없이** 서비스 파라미터의 object 타입을 발견하면 자동으로:
1. import 문 분석
2. 클래스 정의 파일 경로 추적
3. 해당 파일에서 프로퍼티 추출

**프로젝트 내 어디에 정의되어 있든** import 경로만 따라가면 자동 추출됩니다.

### 지원 Import 패턴

| 패턴 | 예시 |
|------|------|
| 같은 파일 | 클래스가 서비스와 같은 파일에 정의 |
| 상대 import | `from .types import MyClass` |
| 절대 import | `from my_module import MyClass` |
| 부모 디렉토리 | `from ..common import MyClass` |

### 제한

- 외부 패키지 (pip install한 것) - 파일 경로 추적 어려움

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
              _parse_imports() ← 서비스 파일의 import 문 분석
                      │
                      ▼
              _resolve_module_to_file() ← 모듈명 → 파일 경로
                      │
                      ▼
              resolve_class_file() ← 클래스 정의 파일 확인
                      │
                      ▼
              extract_types.extract_single_class() ← 프로퍼티 추출
                      │
                      ▼
              types_property_{server}.json 생성
```

---

## 예시

### 서비스 파일 (service.py)

```python
from some_module.data_types import FilterParams  # ← import 추적
from ..common.models import UserConfig           # ← 상대 경로도 지원

@mcp_service(...)
async def query_mail(
    filter_params: FilterParams,  # ← type:"object", class_name:"FilterParams"
    config: UserConfig            # ← type:"object", class_name:"UserConfig"
):
    ...
```

### 자동 추적 과정

```
1. filter_params 파라미터 발견
   → type:"object", class_name:"FilterParams"

2. service.py의 import 문 분석
   → "FilterParams"는 "some_module.data_types"에서 옴

3. 모듈 경로 → 파일 경로 변환
   → /project/some_module/data_types.py

4. data_types.py에서 FilterParams 클래스 프로퍼티 추출
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
      "file": "/path/to/data_types.py",  ← 클래스 정의 파일 (어디든 가능)
      "line": 15,                        ← 정의 라인 번호
      "property_count": 3
    }
  ],
  "properties_by_class": {               ← 클래스별 프로퍼티 그룹
    "FilterParams": [
      {
        "name": "from_address",
        "type": "List[string]",          ← Union[str, List[str]] → List[T]
        "description": "발신자 이메일",
        "examples": [...],
        "default": null
      }
    ]
  },
  "all_properties": [                    ← 전체 프로퍼티 평탄화 목록
    {
      "name": "from_address",
      "type": "List[string]",
      "description": "발신자 이메일",
      "class": "FilterParams",
      "full_path": "FilterParams.from_address"
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

| Python 타입 | 출력 타입 |
|-------------|-----------|
| `str` | `string` |
| `int` | `integer` |
| `float` | `number` |
| `bool` | `boolean` |
| `List[str]` | `List[string]` |
| `List[int]` | `List[integer]` |
| `Dict[K,V]` | `object` |
| `Optional[T]` | T의 타입 |
| `Union[str, List[str]]` | `List[string]` |
| 커스텀 클래스 | `object` |

---

## API 엔드포인트

**`GET /api/graph-types-properties`**

types_property_{server}.json 파일을 읽어서 반환.
파일은 웹 에디터 시작 시 자동 생성됨.

---

## 이전 방식과 비교

| 항목 | 이전 | 현재 |
|------|------|------|
| 추출 기준 | `editor_config.json`의 `types_files` 설정 | 서비스 파라미터 자동 추적 |
| 범위 | 설정된 파일 내 모든 BaseModel | 실제 사용되는 클래스만 |
| 설정 의존 | `types_files` 경로 필수 | 없음 |
| 호출 시점 | API 호출 시 (lazy) | 웹 에디터 시작 시 |
| 클래스 위치 | 설정 파일에 명시된 경로만 | 프로젝트 내 어디든 |

---

## 연관 파일

- `registry_{server}.json` - 서비스 정의 (파라미터에 class_name 포함)
- `types_property_{server}.json` - 참조된 타입 프로퍼티 정보
- `profile_management.py` - 프로필 삭제 시 두 파일 모두 제거
