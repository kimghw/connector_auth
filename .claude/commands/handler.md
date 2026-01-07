> **공통 지침**: 작업 전 [common.md](common.md) 참조

# MCP 핸들러 파라미터 체계 정리

## 파라미터 종류 및 계층 구조

### 1. 파라미터 3단계 구조

#### 1.1 Signature 파라미터 (사용자 입력)
- **정의**: LLM이 직접 제공하는 사용자 입력값
- **위치**: `tool_definition_templates.py`의 `inputSchema`
- **특징**: LLM에게 노출, 최고 우선순위, `targetParam`으로 서비스 메서드에 매핑

#### 1.2 Signature Defaults (파라미터별 기본값)
- **정의**: LLM에게 보이지만 기본값이 있는 파라미터
- **위치**: `tool_definition_templates.py`의 `mcp_service_factors` (source: "signature_defaults")
- **특징**: 2단계(파라미터 객체 변환)에서 병합

#### 1.3 Internal 파라미터 (전역 Internal)
- **정의**: LLM에게 완전히 숨겨진 시스템 고정값
- **위치**: `tool_definition_templates.py`의 `mcp_service_factors` (source: "internal")
- **특징**: `targetParam`으로 서비스 메서드에 매핑, 5단계에서 병합
- **변경사항**: tool_internal_args.json 삭제 → mcp_service_factors로 통합 (2025-01-05)

**런타임 데이터 흐름:**
```
mcp_service_factors (tool_definition_templates.py)
    ↓ generator가 source='internal' 추출
생성된 서버 코드의 INTERNAL_ARGS 딕셔너리 (server_*.py)
    ↓ build_internal_param() 또는 직접 생성자 호출
런타임 파라미터 객체
```

### 2. 서비스 함수 인자
- **정의**: 실제 비즈니스 로직의 메서드 파라미터
- **위치**: `mcp_{service}/{service}_service.py`의 메서드 시그니처

## 매핑 관계

### 2.1 inputSchema → 서비스 메서드 매핑
```
LLM 입력명 → targetParam → 서비스 메서드 파라미터명

예시:
"DatePeriodFilter" → targetParam: "filter_params" → service.mail_list(filter_params=...)
```

### 2.2 Internal 매핑 (mcp_service_factors)
```
mcp_service_factors 키 → targetParam → 서비스 메서드 파라미터

예시:
"select_internal" (source: internal) → select_params → 병합 대상 파라미터
```

## 핸들러 내부 병합 과정 (2번 발생)

### 3.1 첫 번째 병합: Signature 내부 병합 (2단계)
- **시점**: 파라미터 객체 변환 시
- **대상**: Signature Defaults + 사용자 입력
- **우선순위**: 사용자 입력 > Signature Defaults

> **중요**: null/None인 값은 병합에서 제외됨

```python
# 예시: DatePeriodFilter 파라미터 처리
DatePeriodFilter_defaults = {}  # mcp_service_factors에서 가져온 기본값 (source: signature_defaults)
DatePeriodFilter_defaults = {k: v for k, v in DatePeriodFilter_defaults.items() if v is not None}

DatePeriodFilter_user_input = args["DatePeriodFilter"]
DatePeriodFilter_data = merge_param_data(
    DatePeriodFilter_defaults,   # base (null 값 필터링됨)
    DatePeriodFilter_user_input  # overlay - 우선순위 높음
)
```

### 3.2 두 번째 병합: 도구 레벨 병합 (5단계)
- **시점**: Internal 파라미터 처리 후
- **대상**: Internal 파라미터 + Signature 파라미터 객체
- **우선순위**: Signature 파라미터 > Internal
- **조건**: Internal 파라미터 값이 있을 때만 처리

```python
# 예시: select_params 병합
_internal_select = build_internal_param("mail_list_period", "select")  # INTERNAL_ARGS에서

# Signature와 Internal이 같은 targetParam을 가리킬 때만 병합
if "select_params" in call_args:
    existing_value = call_args["select_params"]
    internal_dict = {k: v for k, v in vars(_internal_select).items() if v is not None}
    existing_dict = {k: v for k, v in vars(existing_value).items() if v is not None}
    merged_dict = {**internal_dict, **existing_dict}  # existing이 internal을 덮어씀
    call_args["select_params"] = SelectParams(**merged_dict)
else:
    # Internal만 있는 경우: 값이 있을 때만 추가
    if _internal_select is not None:
        call_args["select_params"] = _internal_select
```

## 실제 데이터 예시

### mail_list 도구의 전체 흐름:

#### 4.1 LLM 입력 (args)
```json
{
  "user_email": "user@example.com",
  "DatePeriodFilter": {
    "received_date_from": "2024-01-01",
    "received_date_to": "2024-01-31"
  }
}
```

#### 4.2 mcp_service_factors (tool_definition_templates.py)
```python
'mcp_service_factors': {
    'select_internal': {
        'source': 'internal',           # LLM에게 완전히 숨김
        'baseModel': 'SelectParams',
        'parameters': {
            'body_preview': {'default': True},
            'subject': {'default': True}
        }
    },
    'filter_defaults': {
        'source': 'signature_defaults', # LLM에게 보이지만 기본값 있음
        'baseModel': 'FilterParams',
        'parameters': {...}
    }
}
```

#### 4.3 최종 서비스 호출
```python
await mail_service.mail_list(
    user_email="user@example.com",
    filter_params=FilterParams(         # DatePeriodFilter에서 매핑됨
        received_date_from="2024-01-01",
        received_date_to="2024-01-31"
    ),
    select_params=SelectParams(         # Internal에서 자동 추가
        body_preview=True,
        subject=True
    )
)
```

## 우선순위 체계

### 최종 우선순위 (높음 → 낮음)
```
1. 사용자 입력 (LLM args)
2. Signature Defaults (mcp_service_factors, source: signature_defaults)
3. Internal 파라미터 (mcp_service_factors, source: internal)
4. 서비스 메서드 기본값
```

## 관련 파일 구조

| 파일 | 역할 | 변경 시점 |
|------|------|----------|
| `tool_definition_templates.py` | LLM inputSchema + mcp_service_factors | 웹에디터 Save 시 |
| `tool_definitions.py` | 클린 도구 정의 (LLM API용) | 웹에디터 Save 시 |
| `registry_{server}.json` | 소스코드 구현 정보 | 소스코드 스캔 시 |
| `{service}_service.py` | 비즈니스 로직 | 개발자가 직접 수정 |

## 핵심 개념

### SIGNATURE vs INTERNAL 핵심 차이

| 모드 | LLM이 값 안 보낼 때 | 결과 |
|------|-------------------|------|
| **SIGNATURE** | `args.get()` → `None` → 서비스에 `None` 전달 | 기본값 미적용 (예: `$select` 없음) |
| **INTERNAL** | `build_internal_param()` → 기본값으로 객체 생성 | 기본값 적용 (예: `$select` 포함) |

#### SIGNATURE 동작
```python
# LLM이 select_params를 안 보내면
select_params_raw = args.get("select_params")  # None
select_params_data = merge_param_data({}, None)  # → None
select_params_params = None  # 서비스에 None 전달
# 결과: $select 파라미터 없이 API 호출 → 모든 필드 반환
```

#### INTERNAL 동작
```python
# INTERNAL_ARGS 딕셔너리에서 기본값으로 객체 생성
_internal_select = build_internal_param("mail_list_period", "select")
# → SelectParams(id=True, subject=True, sender=True, body_preview=True, ...)

# Signature 값이 None이면 Internal 값 사용
if existing_value is None:
    call_args["select_params"] = _internal_select
# 결과: $select=id,subject,sender,... 포함하여 API 호출 → 지정 필드만 반환
```

#### 사용 시나리오
- **SIGNATURE**: LLM이 선택적으로 값을 제공할 때 (사용자가 명시적으로 지정)
- **INTERNAL**: 항상 기본값이 적용되어야 할 때 (시스템 고정값)

### source 필드의 역할 (mcp_service_factors 내)
- `"internal"`: LLM에게 완전히 숨김 - 시스템 고정값
- `"signature_defaults"`: LLM에게 보이지만 기본값 제공

### targetParam의 역할
- **목적**: inputSchema 프로퍼티명과 서비스 메서드 파라미터명 연결
- **사용처**: Signature 파라미터, Internal 파라미터 모두
- **동작**: 핸들러에서 자동 매핑 처리

### targetServiceFactor의 역할 (2026-01-07 추가)
- **목적**: inputSchema 프로퍼티와 mcp_service_factors 항목을 **이름으로** 명시적 연결
- **배경**: 이전에는 타입($ref/baseModel)으로 매칭 → 같은 타입의 파라미터가 여러 개일 때 충돌 발생
- **문제 예시**:
  ```python
  # 두 파라미터가 같은 타입(ExcludeParams)을 사용
  'client_param': {'$ref': '#/$defs/ExcludeParams', ...}  # 클라이언트 필터
  'exclude': {'$ref': '#/$defs/ExcludeParams', ...}       # 제외 조건

  # 타입 매칭 시 'client_param'이 먼저 나오면 잘못된 factor에 매칭됨
  ```
- **해결책**: `targetServiceFactor`로 명시적 연결
  ```python
  'client_param': {
      '$ref': '#/$defs/ExcludeParams',
      'targetParam': 'client_param',           # 서비스 메서드 파라미터
      'targetServiceFactor': 'client_defaults' # mcp_service_factors 키
  },
  'exclude': {
      '$ref': '#/$defs/ExcludeParams',
      'targetParam': 'exclude_params',
      'targetServiceFactor': 'exclude_defaults'  # 다른 factor
  }
  ```

### 매핑 필드 구분

| 필드명 | 용도 | 매핑 대상 |
|--------|------|----------|
| `targetParam` | 서비스 메서드 파라미터명 | `service.method(param_name=...)` |
| `targetServiceFactor` | mcp_service_factors 키 | `mcp_service_factors['factor_key']` |

**매칭 우선순위:**
1. `targetServiceFactor`가 명시된 경우: factor 이름으로 직접 매칭
2. 명시되지 않은 경우: 프로퍼티 이름으로 factor_name 추론

### None 값 처리 원칙 (merge_param_data)

| 조건 | 동작 | 결과 |
|------|------|------|
| `runtime_data`가 falsy (`None`, `{}`, `[]`, `""`) | internal_data 반환 | 기본/내부값 사용 |
| `runtime_data`가 truthy (값 있는 dict) | `{**internal, **runtime}` | runtime이 internal 덮어씀 |
| `runtime_data` dict 내 개별 None 값 | 그대로 병합 | internal 값 덮어씀 (주의!) |

**주의사항:**
- `{"key": None}` 형태는 truthy이므로 internal의 해당 키를 None으로 덮어씀
- 개별 키 레벨의 None 필터링은 5단계 Internal 병합에서만 발생 (`if v is not None`)
- 빈 dict/list/""도 "입력 없음"으로 간주되어 internal 값이 복원됨

## 요약

1. **모든 파라미터 설정이 `tool_definition_templates.py`에 통합**:
   - inputSchema: LLM 노출 스키마
   - mcp_service_factors: Internal + SignatureDefaults (source로 구분)
   - **변경**: tool_internal_args.json 파일 삭제 → mcp_service_factors로 통합

2. **두 번의 병합**:
   - 첫 번째: SignatureDefaults + 사용자 입력 → Signature 파라미터 객체
   - 두 번째: Internal + Signature 파라미터 객체 → 최종 파라미터

3. **source 필드로 파라미터 유형 구분**:
   - `internal`: 숨김
   - `signature_defaults`: 노출 + 기본값

4. **최종 병합 데이터가 서비스 함수에 전달됨**

## 최근 변경사항

### 2026-01-07: targetServiceFactor 도입
- **문제**: 타입 기반 매칭으로 같은 타입의 파라미터 충돌 발생
  - `client_param`과 `exclude` 모두 `ExcludeParams` 타입 사용 시 오매칭
- **해결**: `targetServiceFactor` 필드 추가로 이름 기반 명시적 매칭
- **영향 파일**:
  - `generate_universal_server.py`: 매칭 로직 변경
  - `tool_definition_templates.py`: inputSchema에 targetServiceFactor 추가 가능

### 2025-01-05: Internal Args 처리 방식 변경
- **이전**: `tool_internal_args.json` 파일에서 별도 관리
- **현재**: `tool_definition_templates.py`의 `mcp_service_factors`에 통합
- **추출**: `extract_internal_args_from_tools()` 함수로 source='internal' 파라미터 추출
- **템플릿**: `INTERNAL_ARGS`가 context에서 전달되도록 변경 (파일 로드 제거)

---
*Last Updated: 2026-01-07*
*Version: 1.2*
