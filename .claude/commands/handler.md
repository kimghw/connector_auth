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
_internal_select = build_internal_param("mail_list", "select")  # mcp_service_factors에서

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
# Internal Args에서 기본값으로 객체 생성
_internal_select = build_internal_param("mail_list_period", "select")
# → SelectParams(id=True, subject=True, sender=True, ...)

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

### None 값 처리 원칙
- 병합 시 None 값은 제외됨
- 명시적으로 설정하지 않은 필드는 기존값 유지
- 부분 업데이트 가능

## 요약

1. **모든 파라미터 설정이 `tool_definition_templates.py`에 통합**:
   - inputSchema: LLM 노출 스키마
   - mcp_service_factors: Internal + SignatureDefaults (source로 구분)

2. **두 번의 병합**:
   - 첫 번째: SignatureDefaults + 사용자 입력 → Signature 파라미터 객체
   - 두 번째: Internal + Signature 파라미터 객체 → 최종 파라미터

3. **source 필드로 파라미터 유형 구분**:
   - `internal`: 숨김
   - `signature_defaults`: 노출 + 기본값

4. **최종 병합 데이터가 서비스 함수에 전달됨**
