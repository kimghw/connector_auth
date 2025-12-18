# MCP Tool Default Value Implementation Plan

## 작업 계획: 웹 에디터 초기값 → MCP 도구 적용 로직 구현

---

## 0. 목적

### 0.1 배경

#### 시스템 구조
현재 MCP(Model Context Protocol) 도구 시스템은 다음과 같은 파이프라인으로 동작합니다:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   웹 에디터     │ ──→ │  Jinja 생성기   │ ──→ │   MCP 서버      │
│ (tool_editor)   │     │ (generate_*.py) │     │   (server.py)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
 도구 정의 편집          Python 코드 생성         LLM 요청 처리
```

#### 변수의 두 가지 분류

MCP 도구의 파라미터(변수)는 **LLM에 노출 여부**에 따라 두 가지로 분류됩니다:

| 분류 | 설명 | 특징 |
|------|------|------|
| **Signature 변수** | MCP `inputSchema`에 노출되어 LLM이 인식하고 전달하는 변수 | LLM이 `tools/call` 시 값을 전달 |
| **Internal 변수** | 도구 내부에서만 관리하는 변수 (LLM에 미노출) | 사전 설정된 값으로 동작, LLM 부담 감소 |

#### Signature 변수의 세부 분류

Signature 변수는 다시 **필수 여부**에 따라 구분됩니다:

| 유형 | required 배열 | default 값 | LLM 동작 |
|------|--------------|-----------|---------|
| **Required** | 포함 | 없음 | 반드시 전달해야 함 |
| **Optional (with default)** | 미포함 | 있음 | 전달 안 하면 default 사용 |
| **Optional (without default)** | 미포함 | 없음 | 전달 안 하면 None 사용 |

#### 예시: `handle_query_filter` 도구

```python
# 서비스 함수 시그니처
async def query_filter(
    user_email: str,                              # Required - LLM 필수 전달
    filter: FilterParams,                         # Required - LLM 필수 전달
    exclude: Optional[ExcludeParams] = None,      # Optional - default None
    select: Optional[SelectParams] = None,        # Internal로 전환 가능
    client_filter: Optional[ExcludeParams] = None # Internal로 전환 가능
)
```

위 함수에서:
- `user_email`, `filter`: LLM이 반드시 전달해야 하는 값
- `exclude`: LLM이 선택적으로 전달, 미전달 시 None
- `select`, `client_filter`: 매번 LLM이 전달할 필요 없이 **사전 설정된 기본값**으로 동작하면 효율적

### 0.2 문제점

#### 문제 1: Signature Optional 변수의 default 값 미적용

웹 에디터에서 Optional 변수에 `default` 값을 설정해도, **생성된 코드에서 해당 값이 적용되지 않습니다.**

```
[웹 에디터 설정]
┌─────────────────────────────────────────────────────────────┐
│ Property: "exclude"                                         │
│ ├── Type: object (ExcludeParams)                           │
│ ├── Required: ☐ (선택적)                                   │
│ └── Default: {"exclude_subject_keywords": ["RE:", "FW:"]}  │
└─────────────────────────────────────────────────────────────┘

[저장된 데이터] - tool_definition_templates.py
"exclude": {
    "type": "object",
    "baseModel": "ExcludeParams",
    "default": {"exclude_subject_keywords": ["RE:", "FW:"]}  ← 저장됨
}

[생성된 코드] - server.py (문제!)
exclude = args.get("exclude")  # LLM 미전달 시 None 반환
exclude_params = ExcludeParams(**exclude) if exclude else None
# ↑ default 값 {"exclude_subject_keywords": ["RE:", "FW:"]}가 무시됨!
```

**기대 동작**:
```python
exclude_raw = args.get("exclude")
if exclude_raw is not None:
    exclude_params = ExcludeParams(**exclude_raw)
else:
    # Default value from web editor
    exclude_params = ExcludeParams(**{"exclude_subject_keywords": ["RE:", "FW:"]})
```

#### 문제 2: Internal 변수 초기값 할당 로직 검증 필요

Internal 변수는 `tool_internal_args.json`에 값이 저장되고, Jinja 템플릿에서 코드가 생성됩니다.
현재 구현은 완료되었으나, **실제 생성된 코드가 올바르게 동작하는지 검증이 필요**합니다.

```
[tool_internal_args.json]
{
    "handle_query_filter": {
        "select": {
            "type": "SelectParams",
            "value": {"id": true, "subject": true, "from": true}
        }
    }
}

[생성되어야 하는 코드]
# Internal Args
select_params = SelectParams(**{"id": True, "subject": True, "from": True})
```

#### 문제 3: 값 할당 우선순위 명확화 필요

현재 다음 상황에서 어떤 값을 사용해야 하는지 명확한 규칙이 없습니다:

| 상황 | 현재 동작 | 기대 동작 |
|------|----------|----------|
| LLM이 값 전달 | 전달된 값 사용 ✅ | 전달된 값 사용 |
| LLM 미전달 + default 있음 | None 사용 ❌ | **default 값 사용** |
| LLM 미전달 + default 없음 | None 사용 ✅ | None 사용 |
| Internal 변수 | internal_args 값 사용 ✅ | internal_args 값 사용 |

### 0.3 목표

#### 핵심 목표

**웹 에디터에서 설정한 초기값(default)이 MCP 도구 실행 시 정상적으로 적용되도록 한다.**

#### 세부 목표

| # | 목표 | 대상 | 작업 내용 |
|---|------|------|----------|
| **G1** | Signature Optional default 적용 | Jinja 생성기 + 템플릿 | `inputSchema.properties.{param}.default` 값을 코드 생성 시 반영 |
| **G2** | Internal 변수 할당 로직 검증 | Jinja 템플릿 | `tool_internal_args.json` 값이 올바르게 코드에 삽입되는지 확인 |
| **G3** | 웹 에디터 UI 보강 | tool_editor.html | Optional 변수에 default 값 입력 UI 제공 |
| **G4** | 값 우선순위 규칙 정립 | 문서화 + 구현 | LLM 전달값 > default > None 순서 명확화 |

#### 목표별 상세 설명

**G1. Signature Optional default 적용**

```python
# 현재 (문제)
exclude = args.get("exclude")
exclude_params = ExcludeParams(**exclude) if exclude else None

# 목표 (수정 후)
exclude_raw = args.get("exclude")
if exclude_raw is not None:
    exclude_params = ExcludeParams(**exclude_raw)
else:
    exclude_params = ExcludeParams(**{"exclude_subject_keywords": ["RE:", "FW:"]})
```

**G2. Internal 변수 할당 로직 검증**

```python
# tool_internal_args.json 설정값이 아래처럼 생성되어야 함
select_params = SelectParams(**{"id": True, "subject": True, "from": True})
client_filter_params = ExcludeParams(**{"exclude_subject_keywords": []})
```

**G3. 웹 에디터 UI 보강**

```
┌─────────────────────────────────────────────────────────────┐
│ Property: "exclude"                                         │
│ ├── Type: [object ▼] BaseModel: [ExcludeParams ▼]          │
│ ├── Required: ☐                                            │
│ ├── Destination: ● Signature  ○ Internal                   │
│ └── Default Value: ┌────────────────────────────────┐      │
│                    │ {                              │      │
│                    │   "exclude_subject_keywords":  │      │
│                    │   ["RE:", "FW:"]               │      │
│                    │ }                              │      │
│                    └────────────────────────────────┘      │
│                    ↑ Required=false일 때만 표시            │
└─────────────────────────────────────────────────────────────┘
```

**G4. 값 우선순위 규칙 정립**

> **중요**: Signature 변수와 Internal 변수는 **별개의 트랙**입니다. Internal 변수는 LLM에 노출되지 않으므로 LLM 전달값과 우선순위를 비교하지 않습니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    파라미터 유형별 값 결정                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Signature 변수] - LLM에 노출됨                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. LLM이 전달한 값 (args에서 추출, not None인 경우)     │   │
│  │ 2. 웹 에디터 default 값 (inputSchema.properties.default)│   │
│  │ 3. None (기본값 없는 Optional)                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Internal 변수] - LLM에 미노출 (별개 트랙)                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 항상 tool_internal_args.json 값 사용                    │   │
│  │ (LLM 전달값 자체가 없음 - inputSchema에 미포함)         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 0.4 기대 효과

#### 정성적 효과

| 효과 | 설명 |
|------|------|
| **LLM 부담 감소** | 매번 모든 파라미터를 전달할 필요 없음. 필수값만 전달하면 나머지는 기본값 적용 |
| **설정 유연성 증가** | 코드 수정 없이 웹 에디터에서 기본값 변경 가능 |
| **운영 편의성** | 서버 재시작 없이 `generate_server.py` 실행만으로 새 설정 적용 |
| **일관된 동작** | 값 우선순위가 명확해져 예측 가능한 도구 동작 보장 |

#### 정량적 효과 (예상)

```
Before: LLM이 전달해야 하는 파라미터
┌─────────────────────────────────────────────────────────────┐
│ handle_query_filter({                                       │
│   "user_email": "...",        // Required                   │
│   "filter": {...},            // Required                   │
│   "exclude": {...},           // Optional - 매번 전달 필요  │
│   "select": {...},            // Optional - 매번 전달 필요  │
│   "client_filter": {...}      // Optional - 매번 전달 필요  │
│ })                                                          │
│                                                             │
│ → 5개 파라미터 전달 필요                                    │
└─────────────────────────────────────────────────────────────┘

After: default/internal 적용 시
┌─────────────────────────────────────────────────────────────┐
│ handle_query_filter({                                       │
│   "user_email": "...",        // Required                   │
│   "filter": {...}             // Required                   │
│   // exclude: default 적용                                  │
│   // select: internal 적용                                  │
│   // client_filter: internal 적용                           │
│ })                                                          │
│                                                             │
│ → 2개 파라미터만 전달 (60% 감소)                            │
└─────────────────────────────────────────────────────────────┘
```

#### 값 결정 흐름도

```
MCP 도구 호출 시 파라미터 값 결정 로직:
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  파라미터 유형 확인                                                 │
│         │                                                           │
│         ├── Internal 변수인가?                                      │
│         │         │                                                 │
│         │         └── YES → tool_internal_args.json 값 사용         │
│         │                   (LLM 전달값 무시)                       │
│         │                                                           │
│         └── Signature 변수                                          │
│                   │                                                 │
│                   ├── LLM이 값 전달했는가?                          │
│                   │         │                                       │
│                   │         └── YES → 전달된 값 사용                │
│                   │                                                 │
│                   └── LLM이 값 미전달                               │
│                             │                                       │
│                             ├── default 값 있는가?                  │
│                             │         │                             │
│                             │         └── YES → default 값 사용     │
│                             │                                       │
│                             └── default 값 없음                     │
│                                       │                             │
│                                       └── None 사용                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Before/After 비교

| 항목 | Before | After |
|------|--------|-------|
| Signature Optional default | 무시됨 (None 반환) | 적용됨 |
| Internal 변수 | 구현됨 (검증 필요) | 검증 완료 |
| 웹 에디터 default UI | 없음 | Optional 변수에 제공 |
| 값 우선순위 | 불명확 | 명확한 규칙 정립 |
| LLM 파라미터 전달 | 모든 파라미터 | 필수 파라미터만 |

---

## 1. 현재 상황 분석

### 1.1 변수 분류 체계

| 분류 | 설명 | 저장 위치 | MCP 노출 | 초기값 처리 |
|------|------|----------|----------|------------|
| **Signature (Required)** | LLM이 필수로 전달해야 하는 변수 | `inputSchema.properties` + `required[]` | O | 없음 (필수) |
| **Signature (Optional + Default)** | LLM이 선택적으로 전달, 미전달 시 기본값 사용 | `inputSchema.properties` + `default` | O | **❌ 미구현** |
| **Internal** | LLM에 미노출, 내부에서만 사용 | `tool_internal_args.json` | X | **✅ 구현됨** |

### 1.2 문제점

```
웹 에디터에서 설정 가능한 값:
┌─────────────────────────────────────────────────────────────┐
│ Property: "filter"                                          │
│ ├── Type: object (FilterParams)                            │
│ ├── Required: ☐ (선택적)                                   │
│ ├── Default: { "subject": "test" }  ← 웹에서 설정 가능     │
│ └── Destination: [Signature] / [Internal]                  │
└─────────────────────────────────────────────────────────────┘

현재 코드 생성 결과 (문제):
┌─────────────────────────────────────────────────────────────┐
│ # Signature (Optional) - Default 값이 적용 안됨!            │
│ filter = args.get("filter")   ← None 반환 (기본값 무시)    │
│ filter_params = FilterParams(**filter) if filter else None │
│                                                             │
│ # Internal - Default 값이 정상 적용됨 ✅                    │
│ select_params = SelectParams(**{"id": true, ...})          │
└─────────────────────────────────────────────────────────────┘
```

**핵심 문제**: Signature 변수의 `default` 값이 코드 생성 시 무시됨

---

## 2. 목표

### 2.1 수정 후 기대 동작

```python
# 시나리오 1: LLM이 값을 전달한 경우
args = {"filter": {"subject": "meeting"}}
filter_params = FilterParams(**args["filter"])  # LLM 값 사용

# 시나리오 2: LLM이 값을 전달하지 않은 경우 (Optional + Default)
args = {}
filter_params = FilterParams(**{"subject": "test"})  # 웹 에디터 기본값 사용

# 시나리오 3: Internal 변수 (항상 기본값)
select_params = SelectParams(**{"id": true, ...})  # 항상 internal_args 값 사용
```

### 2.2 적용 우선순위

> **참고**: 이 우선순위는 **Signature 변수**에만 적용됩니다. Internal 변수는 항상 `tool_internal_args.json` 값을 사용합니다.

```
Signature 변수 값 결정 (높음 → 낮음):

1. LLM이 전달한 값 (args에서 추출, not None인 경우)
   └─ 빈 객체 {}, 빈 배열 [], 0, false도 유효한 값으로 처리

2. 웹 에디터에서 설정한 default 값 (has_default가 true인 경우)
   └─ inputSchema.properties.{param}.default
   └─ default: null도 명시적 기본값으로 처리

3. None (기본값 미정의 시)
   └─ has_default가 false인 Optional 변수
```

> **⚠️ 주의**: "타입의 기본 생성자 (빈 객체 {})"는 우선순위에 포함하지 않습니다.
> - 스칼라 타입(string, integer)에는 적용 불가
> - 암묵적 기본값은 예측 불가능한 동작을 유발
> - 최종 fallback은 항상 **None**

---

## 3. 구현 방안 비교

### 방안 A: Template에 Default 값 직접 하드코딩 (권장 ⭐)

**장점**:
- 단순하고 명확
- 런타임 파일 읽기 불필요
- 생성된 코드만으로 동작 완결

**단점**:
- 기본값 변경 시 서버 재생성 필요

```python
# 생성되는 코드 예시
filter = args.get("filter")
if filter is not None:
    filter_params = FilterParams(**filter)
else:
    # Default from web editor
    filter_params = FilterParams(**{"subject": "test"})
```

### 방안 B: 런타임에 tool_internal_args.json 읽기

**장점**:
- 서버 재생성 없이 기본값 변경 가능

**단점**:
- 파일 읽기 오버헤드
- 파일 경로 관리 복잡
- 파일 없을 시 오류 처리 필요

### 방안 C: 함수 시그니처에 Default 값 포함

**장점**:
- Python 방식에 충실

**단점**:
- 복잡한 객체 타입 기본값 표현 어려움
- 함수 정의가 매우 길어짐

---

## 4. 선택: 방안 A (Template 하드코딩) + 확장

Jinja 템플릿에서 default 값을 직접 코드에 포함시키되,
`inputSchema.properties.{param}.default`에서 가져오도록 수정

---

## 5. 상세 구현 계획

### Phase 1: Jinja 생성기 수정 (`generate_outlook_server.py`)

#### 1.1 `analyze_tool_schema()` 함수 수정

**파일**: `jinja/generate_outlook_server.py`
**위치**: 라인 284-434

**현재 코드**:
```python
for param_name, param_info in properties.items():
    analyzed['params'][param_name] = {
        'name': param_name,
        'is_required': param_name in required,
        'has_default': 'default' in param_info,
        'default': param_info.get('default')
    }
```

**수정 목표**:
- `default` 값을 object_params에도 저장
- default 값의 타입 정보 보존
- **명시적 `null` 기본값 지원** (`default: null`을 감지하기 위해 키 존재 여부로 판단)

**수정 후**:
```python
for param_name, param_info in properties.items():
    # ⚠️ 중요: 'default' in param_info로 키 존재 여부를 먼저 확인
    # param_default is not None으로 판단하면 default: null을 감지 못함
    has_default = 'default' in param_info
    param_default = param_info.get('default')

    analyzed['params'][param_name] = {
        'name': param_name,
        'is_required': param_name in required,
        'has_default': has_default,
        'default': param_default,
        # default_json: None 자체도 유효한 기본값이므로 has_default 기준으로 생성
        'default_json': json.dumps(param_default) if has_default else None
    }

    # Object params에도 default 정보 추가
    if param_name in analyzed['object_params']:
        analyzed['object_params'][param_name]['has_default'] = has_default
        analyzed['object_params'][param_name]['default'] = param_default
```

> **참고**: `default: null`과 `default 키 없음`은 다른 의미입니다.
> - `default: null` → 명시적으로 None을 기본값으로 사용
> - `default 키 없음` → 기본값 미정의, LLM 미전달 시 에러 또는 None 처리

#### 1.2 테스트 케이스

```bash
# 테스트: default 값이 분석 결과에 포함되는지 확인
python -c "
from generate_outlook_server import analyze_tool_schema

# 테스트 도구 정의
test_tool = {
    'name': 'test_tool',
    'inputSchema': {
        'properties': {
            'filter': {
                'type': 'object',
                'baseModel': 'FilterParams',
                'default': {'subject': 'test'}  # 기본값 있음
            },
            'user_email': {
                'type': 'string'  # 기본값 없음
            }
        },
        'required': ['user_email']
    }
}

result = analyze_tool_schema(test_tool, {})
print('filter default:', result['object_params']['filter'].get('default'))
print('filter has_default:', result['object_params']['filter'].get('has_default'))
"
```

---

### Phase 2: Jinja 템플릿 수정 (`outlook_server_template.jinja2`)

#### 2.1 Object Parameter 처리 로직 수정

**파일**: `jinja/outlook_server_template.jinja2`
**위치**: 라인 346-448

**현재 코드** (문제):
```jinja2
{%- for param_name, param_info in tool.object_params.items() %}
{%- if param_name not in tool.internal_args %}
{%- if param_info.is_optional %}
{{ param_name }}_params = None
if {{ param_name }}:
    {{ param_name }}_params = {{ param_info.class_name }}(**{{ param_name }})
{%- endif %}
{%- endif %}
{%- endfor %}
```

**수정 후**:
```jinja2
{%- for param_name, param_info in tool.object_params.items() %}
{%- if param_name not in tool.internal_args %}
    {#- Required parameter #}
    {%- if not param_info.is_optional %}
    {{ param_name }}_params = {{ param_info.class_name }}(**args["{{ param_name }}"])

    {#- Optional parameter with default value (has_default로 판단, default: null 포함) #}
    {%- elif param_info.has_default %}
    {{ param_name }}_raw = args.get("{{ param_name }}")
    if {{ param_name }}_raw is not None:
        {#- LLM이 값을 전달한 경우 (빈 객체 {}, 빈 배열 []도 유효한 값으로 처리) #}
        {{ param_name }}_params = {{ param_info.class_name }}(**{{ param_name }}_raw)
    else:
        {#- LLM 미전달 시 default 값 사용 (default: null이면 None) #}
        {%- if param_info.default is not none %}
        {{ param_name }}_params = {{ param_info.class_name }}(**{{ param_info.default | pprint }})
        {%- else %}
        {{ param_name }}_params = None
        {%- endif %}

    {#- Optional parameter without default #}
    {%- else %}
    {{ param_name }}_raw = args.get("{{ param_name }}")
    {#- ⚠️ is not None으로 체크해야 빈 객체 {}, 빈 배열 []이 None으로 변환되지 않음 #}
    {{ param_name }}_params = {{ param_info.class_name }}(**{{ param_name }}_raw) if {{ param_name }}_raw is not None else None
    {%- endif %}
{%- endif %}
{%- endfor %}
```

> **⚠️ 수정 포인트 (피드백 반영)**:
>
> | 문제 | 원인 | 수정 |
> |------|------|------|
> | `default: null` 무시됨 | `param_info.default is not none` 조건이 null을 제외 | `has_default`로만 분기, 내부에서 null 처리 |
> | `{}`, `[]`, `0`, `False` → None 변환 | `if param_raw` (falsy 체크) | `if param_raw is not None` (None 체크) |

#### 2.2 일반 Parameter (string, integer 등) 처리 수정

**현재 코드**:
```jinja2
{%- if param_info.is_required %}
{{ param_name }} = args["{{ param_name }}"]
{%- else %}
{{ param_name }} = args.get("{{ param_name }}")
{%- endif %}
```

**수정 후**:
```jinja2
{%- if param_info.is_required %}
{{ param_name }} = args["{{ param_name }}"]
{%- elif param_info.has_default %}
{#- ⚠️ 정책 결정: LLM의 명시적 null 처리 방식 #}
{#- args.get(name, default)는 키 존재 + 값이 None이면 기본값 적용 안 됨 #}
{#- LLM이 명시적으로 null을 전달한 경우 기본값으로 대체하려면 아래 로직 사용 #}
{{ param_name }}_raw = args.get("{{ param_name }}")
{{ param_name }} = {{ param_name }}_raw if {{ param_name }}_raw is not None else {{ param_info.default | pprint }}
{%- else %}
{{ param_name }} = args.get("{{ param_name }}")
{%- endif %}
```

> **정책 결정 필요**: LLM이 명시적으로 `null`을 전달했을 때의 처리
>
> | 정책 | 설명 | 코드 |
> |------|------|------|
> | **A. LLM null 존중** | LLM이 null 보내면 None 사용 | `args.get(name, default)` |
> | **B. null도 기본값 대체** | LLM이 null 보내도 기본값 사용 | `val if val is not None else default` |
>
> **권장**: 정책 B (null도 기본값 대체) - Object 파라미터와 일관된 동작

#### 2.3 생성 결과 예시

**Before**:
```python
async def handle_query_filter(args: Dict[str, Any]) -> Dict[str, Any]:
    filter = args.get("filter")  # None 반환 가능
    filter_params = FilterParams(**filter) if filter else None  # 기본값 없음
```

**After**:
```python
async def handle_query_filter(args: Dict[str, Any]) -> Dict[str, Any]:
    filter_raw = args.get("filter")
    if filter_raw is not None:
        filter_params = FilterParams(**filter_raw)
    else:
        # Default value from web editor
        filter_params = FilterParams(**{"subject": "test"})
```

---

### Phase 3: 웹 에디터 프론트엔드 수정

#### 3.1 Default 값 입력 UI

**파일**: `mcp_editor/templates/tool_editor.html`

**목표**:
- Signature 변수에도 default 값 설정 UI 제공
- Required가 아닌 경우에만 default 입력 가능

**UI 수정 위치**: `renderPropertyEditor()` 함수

```html
<!-- Required가 아닌 경우 Default 값 입력 필드 표시 -->
<div class="form-group" id="default-value-group-${propName}"
     style="${prop.isRequired ? 'display:none' : ''}">
    <label>Default Value (JSON)</label>
    <textarea class="form-control default-value-input"
              data-prop="${propName}"
              placeholder='예: {"subject": "test"} 또는 "문자열" 또는 0'
              rows="3">${formatDefaultValue(prop.default)}</textarea>
    <small class="text-muted">
        LLM이 값을 전달하지 않을 때 사용할 기본값 (JSON 형식)
    </small>
</div>

<script>
// ⚠️ 중요: falsy 스칼라 값(0, "", false, [])을 올바르게 처리
function formatDefaultValue(defaultVal) {
    // undefined면 빈 문자열 반환
    if (defaultVal === undefined) {
        return '';
    }
    // null, 0, "", false, [] 등 모든 값을 JSON으로 변환
    return JSON.stringify(defaultVal, null, 2);
}
</script>
```

> **⚠️ 주의**: `prop.default || {}`는 falsy 스칼라 값을 덮어씁니다!
>
> | 실제 기본값 | `prop.default \|\| {}` 결과 | 올바른 처리 |
> |------------|---------------------------|------------|
> | `0` | `{}` ❌ | `0` |
> | `""` | `{}` ❌ | `""` |
> | `false` | `{}` ❌ | `false` |
> | `[]` | `{}` ❌ | `[]` |
> | `null` | `{}` ❌ | `null` |
>
> **해결**: `defaultVal === undefined` 체크 후 `JSON.stringify()` 사용

#### 3.2 Required 토글 시 Default 필드 연동

```javascript
function toggleRequired(toolIdx, propName) {
    const isRequired = /* 새로운 required 상태 */;
    const defaultGroup = document.getElementById(`default-value-group-${propName}`);

    if (isRequired) {
        // Required면 default 입력 숨기고 값 제거
        defaultGroup.style.display = 'none';
        delete tools[toolIdx].inputSchema.properties[propName].default;
    } else {
        // Optional이면 default 입력 표시
        defaultGroup.style.display = 'block';
    }
}
```

#### 3.3 저장 시 Default 값 검증

```javascript
function saveTools() {
    // 각 property의 default 값이 유효한 JSON인지 검증
    for (const tool of tools) {
        for (const [propName, prop] of Object.entries(tool.inputSchema.properties || {})) {
            if (prop.default !== undefined) {
                try {
                    // 문자열이면 JSON 파싱 검증
                    if (typeof prop.default === 'string') {
                        prop.default = JSON.parse(prop.default);
                    }
                } catch (e) {
                    alert(`Invalid JSON in default value for ${propName}`);
                    return;
                }
            }
        }
    }
    // ... 저장 로직
}
```

---

### Phase 4: Internal vs Signature Default 값 통합 검증

#### 4.1 데이터 흐름 확인

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 웹 에디터                                                               │
│                                                                         │
│  Signature Property:                                                    │
│  ├── Required=false → default 값 입력 가능                              │
│  └── 저장 시 → inputSchema.properties.{name}.default에 저장             │
│                                                                         │
│  Internal Property:                                                     │
│  └── 저장 시 → tool_internal_args.json.{tool}.{name}.value에 저장       │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Jinja 생성기 (generate_outlook_server.py)                               │
│                                                                         │
│  analyze_tool_schema():                                                 │
│  ├── properties.{name}.default 읽기 → object_params[name]['default']    │
│  └── internal_args[tool][name].value 읽기 → internal_args[name]         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Jinja 템플릿 (outlook_server_template.jinja2)                           │
│                                                                         │
│  생성 코드:                                                              │
│  ├── Signature (optional+default): args.get() || default 값 사용        │
│  └── Internal: 항상 internal_args 값 사용                               │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 4.2 통합 테스트 시나리오

| # | 시나리오 | 입력 | 기대 결과 |
|---|----------|------|----------|
| 1 | Signature Required | `args["filter"]` | LLM 값 사용 (필수) |
| 2 | Signature Optional + Default + LLM 전달 | `args.get("filter")` = 값 있음 | LLM 값 사용 |
| 3 | Signature Optional + Default + LLM 미전달 | `args.get("filter")` = None | Default 값 사용 |
| 4 | Signature Optional + No Default + LLM 미전달 | `args.get("filter")` = None | None 사용 |
| 5 | Internal | 항상 | internal_args.value 사용 |

---

## 6. 파일 수정 목록

| 파일 | 수정 내용 | 우선순위 |
|------|----------|---------|
| `jinja/generate_outlook_server.py` | `analyze_tool_schema()`에 default 값 처리 추가 | 1 |
| `jinja/outlook_server_template.jinja2` | Object/일반 param의 default 처리 로직 | 2 |
| `mcp_editor/templates/tool_editor.html` | Default 값 입력 UI 추가 | 3 |
| `mcp_editor/tool_editor_web.py` | Default 값 저장/로드 검증 | 4 |

---

## 7. 체크리스트

### Phase 1: Jinja 생성기
- [ ] `analyze_tool_schema()`에서 `default` 값 추출
- [ ] `object_params`에 `has_default`, `default` 필드 추가
- [ ] 단위 테스트

### Phase 2: Jinja 템플릿
- [ ] Object parameter default 처리 로직 수정
- [ ] 일반 parameter default 처리 로직 수정
- [ ] 코드 생성 테스트

### Phase 3: 웹 에디터
- [ ] Default 값 입력 UI 추가
- [ ] Required 토글과 연동
- [ ] JSON 유효성 검증
- [ ] 저장/로드 테스트

### Phase 4: 통합 테스트
- [ ] E2E 테스트 시나리오 실행
- [ ] 5가지 시나리오 모두 통과 확인

---

## 8. 대안 검토: 템플릿에 변수 지정 방식

> "template에 변수가 지정되어 있는데 여기에 초기값을 넣어두고 함수로 불러오는게 간단해 보일 수도 있긴한데"

### 장점
- 구현이 단순함
- 모든 default 값이 한 곳에 집중

### 단점
- **관리 분산**: 웹 에디터 ↔ 템플릿 파일 이중 관리
- **동기화 문제**: 웹에서 변경해도 템플릿 수동 수정 필요
- **유지보수 어려움**: 어디서 값이 오는지 추적 곤란

### 결론
**권장하지 않음**. 웹 에디터에서 설정한 값이 자동으로 코드에 반영되는 현재 아키텍처가 더 적합합니다. 다만, 모든 default 값을 한 곳에서 관리하고 싶다면 `tool_internal_args.json`을 확장하는 것이 나음.

---

## 9. 추가 고려사항

### 9.1 Nested Properties의 Default 값

현재 `client_filter.properties`처럼 nested 구조의 default 값도 지원해야 함:

```json
{
    "client_filter": {
        "type": "object",
        "properties": {
            "exclude_subject": {
                "type": "array",
                "default": ["RE:", "FW:"]
            }
        },
        "default": {
            "exclude_subject": ["RE:", "FW:"]
        }
    }
}
```

### 9.2 타입별 Default 값 표현

| 타입 | Default 값 예시 | 코드 생성 |
|------|----------------|----------|
| string | `"default text"` | `args.get("param", "default text")` |
| integer | `10` | `args.get("param", 10)` |
| boolean | `false` | `args.get("param", False)` |
| array | `["a", "b"]` | `args.get("param", ["a", "b"])` |
| object | `{"key": "val"}` | `TypeClass(**{"key": "val"})` |

---

## 10. 예상 소요 시간

| Phase | 작업 | 예상 작업량 |
|-------|------|-----------|
| 1 | Jinja 생성기 수정 | 소 |
| 2 | Jinja 템플릿 수정 | 중 |
| 3 | 웹 에디터 UI | 중 |
| 4 | 통합 테스트 | 소 |

---

## 11. 수정 범위 (Scope)

### 11.1 수정 대상 (In Scope)

본 작업은 **프레젠테이션 레이어**와 **코드 생성 레이어**만 수정합니다.

| 레이어 | 파일 | 수정 내용 |
|--------|------|----------|
| **웹 에디터** | `mcp_editor/templates/tool_editor.html` | Optional 변수에 default 값 입력 UI 추가 |
| **웹 에디터 백엔드** | `mcp_editor/tool_editor_web.py` | Default 값 저장/로드 검증 (필요시) |
| **Jinja 생성기** | `jinja/generate_outlook_server.py` | `analyze_tool_schema()`에서 default 값 추출 |
| **Jinja 템플릿** | `jinja/outlook_server_template.jinja2` | default 값 적용하는 코드 생성 |
| **도구 정의** | `jinja/tool_definition_templates.py` | default 값 저장 (웹 에디터에서 자동 저장) |
| **Internal Args** | `jinja/tool_internal_args.json` | Internal 변수 값 저장 (웹 에디터에서 자동 저장) |

### 11.2 수정 금지 대상 (Out of Scope)

**비즈니스 로직 및 서비스 레이어는 절대 수정하지 않습니다.**

| 레이어 | 파일/폴더 | 이유 |
|--------|----------|------|
| **서비스 함수** | `services/*.py` | 비즈니스 로직 - 변경 시 전체 시스템 영향 |
| **MCP 핸들러** | `mcp_outlook/mcp_server/outlook_handlers.py` | 서비스 호출 로직 - 생성 코드가 아님 |
| **Pydantic 모델** | `models/*.py`, `FilterParams`, `ExcludeParams` 등 | 데이터 구조 정의 - 변경 시 호환성 문제 |
| **인증/토큰** | `services/auth_service.py`, `token_manager.py` | 보안 관련 - 영향도 높음 |
| **데이터베이스** | `database/*.py` | 데이터 영속성 - 영향도 높음 |

### 11.3 아키텍처 관점에서의 수정 범위

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              수정 범위 (In Scope)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐      │
│   │   웹 에디터     │ ──→ │  Jinja 생성기   │ ──→ │  생성된 코드    │      │
│   │ (tool_editor)   │     │ (generate_*.py) │     │  (server.py)    │      │
│   │                 │     │                 │     │                 │      │
│   │ ✅ 수정 대상    │     │ ✅ 수정 대상    │     │ ✅ 자동 생성    │      │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            수정 금지 (Out of Scope)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐      │
│   │  서비스 레이어  │     │  Pydantic 모델  │     │   데이터베이스  │      │
│   │  (services/)    │     │  (models/)      │     │  (database/)    │      │
│   │                 │     │                 │     │                 │      │
│   │ ❌ 수정 금지    │     │ ❌ 수정 금지    │     │ ❌ 수정 금지    │      │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘      │
│                                                                             │
│   ┌─────────────────┐     ┌─────────────────┐                              │
│   │  MCP 핸들러     │     │  인증/토큰      │                              │
│   │ (outlook_       │     │ (auth_service,  │                              │
│   │  handlers.py)   │     │  token_manager) │                              │
│   │ ❌ 수정 금지    │     │ ❌ 수정 금지    │                              │
│   └─────────────────┘     └─────────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.4 수정 원칙

1. **단방향 데이터 흐름 유지**: 웹 에디터 → Jinja 생성기 → MCP 서버 코드
2. **비즈니스 로직 분리**: 서비스 함수는 파라미터를 받아 처리하는 역할만 담당
3. **코드 생성 레이어에서 해결**: default 값 적용은 생성된 MCP 서버 코드에서 처리
4. **서비스 함수 시그니처 유지**: `query_filter(user_email, filter, exclude, select, client_filter)` 변경 없음

---

## 12. 결론

**핵심 수정 포인트**:

1. **`generate_outlook_server.py`**: `analyze_tool_schema()`에서 `inputSchema.properties.{param}.default` 값을 추출하여 `object_params`에 저장

2. **`outlook_server_template.jinja2`**: Optional parameter 처리 시 default 값이 있으면 fallback으로 사용하는 코드 생성

3. **`tool_editor.html`**: Required가 아닌 property에 대해 default 값 입력 UI 제공

이 세 가지 수정으로 웹 에디터에서 설정한 초기값이 MCP 도구 실행 시 정상적으로 적용됩니다.

**수정 범위 요약**: 웹 에디터, Jinja 생성기, Jinja 템플릿만 수정하며, 비즈니스 로직(서비스 함수, 모델, 핸들러)은 절대 수정하지 않습니다.
