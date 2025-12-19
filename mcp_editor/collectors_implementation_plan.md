# MCPMetaRegistry Collectors 구현 계획

## 0. 목표 (Jinja 템플릿 자동화 관점)

최종 목적은 `jinja/generate_{server_name}_server.py`가 Jinja 템플릿에 넘기는 **context 데이터를 안정적으로 만들어주는 “수집/정규화 관리자”**를 갖추는 것이다.

즉, MCPMetaRegistry의 산출물은 아래 형태 중 하나로 귀결되어야 한다:

1) **(권장) 템플릿 context를 그대로 생성**  
   - `tools`, `services`, `param_types`, `modules`, `internal_args`, `server_name`, `handler_instances`
   - 현재 `jinja/generate_outlook_server.py`가 `analyze_tool_schema()`/`extract_service_metadata()`를 통해 만들고 있는 구조와 동일

2) **(대안) generator가 context를 만들 수 있게 입력을 “완전한 형태”로 제공**  
   - `tool_definition_templates.py`의 각 tool에 `mcp_service`/`baseModel`/defaults 등을 정확히 채워서 generator의 휴리스틱 의존을 제거

템플릿(outlook/file_handler 등)은 `tool.params`, `tool.object_params`, `tool.call_params`, `tool.handler.*`, `tool.internal_args` 등에 강하게 의존하므로, “수집”만이 아니라 **템플릿이 요구하는 데이터 구조로의 정규화/분석 단계(tool analyzer)** 가 핵심이다.

## 1. 구조 개요
```
mcp_editor/
├── mcp_meta_registry/
│   ├── __init__.py
│   ├── registry.py                 # 메인 레지스트리 클래스
│   └── collectors/
│       ├── __init__.py
│       ├── base.py                 # BaseCollector 추상 클래스
│       ├── tool_definitions_collector.py   # MCP_TOOLS 로딩(.py/.json) + 최소 정규화
│       ├── internal_args_collector.py      # tool_internal_args.json 로딩 + defaults 보강
│       ├── service_scanner_collector.py    # @mcp_service AST 스캔(시그니처/파라미터)
│       ├── pydantic_models_collector.py    # BaseModel 로드 + Schema 생성(선택)
│       └── tool_analyzer_collector.py      # tool.params/object_params/call_params/handler 분석(템플릿 계약)
```

## 2. 기존 코드와의 매핑 관계

### collectors/service_scanner_collector.py ← mcp_service_scanner.py
- **재사용 가능**:
  - AST 트리 파싱 로직
  - 데코레이터 감지 알고리즘
- **수정 필요**:
  - 출력 스키마를 “템플릿/분석기에서 바로 쓰는 파라미터 구조”로 고정  
    (`name/type/has_default/default/is_required` 형태 권장)
  - server별 scan_dir/skip_parts를 context로 주입

### collectors/tool_analyzer_collector.py ← jinja/generate_outlook_server.py (analyze_tool_schema)
- **핵심**: 템플릿이 요구하는 `tool.params`, `tool.object_params`, `tool.call_params`, `tool.handler.*`를 생성
- **이관/공유 포인트**:
  - inputSchema.required/default + mcp_service.parameters(구조화된 파라미터) 병합 규칙
  - object param(baseModel) 판별 규칙(휴리스틱 최소화)
  - internal_args를 call_params에 합치는 규칙(템플릿에서 `{arg}_params` 사용)

### collectors/pydantic_models_collector.py ← pydantic_to_schema.py (+ extract_types.py 일부)
- **재사용 가능**:
  - Pydantic 모델 분석
  - JSON Schema 생성
- **수정 필요**:
  - server별 `types_files`를 context로 주입(editor_config 기반)
  - generator가 필요로 하는 최소 정보에 집중  
    (예: `param_types` 집합, baseModel 지정, internal arg type 검증)

### collectors/tool_definitions_collector.py (신규, but 기존 loader 로직 재사용 권장)
- **목적**: tool_definition_templates(.py) / tool_definitions(.py/.json)에서 MCP_TOOLS 로드
- **주의**: import 실행 없이 AST 기반 로딩(현재 generator 방식 유지)

### collectors/internal_args_collector.py (신규)
- **목적**: tool_internal_args.json 로드 + `original_schema.properties.default` 기반 defaults 보강
- **템플릿 요구**: `type`, `value`, `original_schema` 키 존재 여부/형식 정규화

## 3. 구현 순서

### Phase 1: 기본 구조 설정
1. `mcp_meta_registry/` 디렉토리 생성
2. `__init__.py` 파일들 생성
3. `base.py` - BaseCollector 추상 클래스 정의

### Phase 2: 핵심 수집기 구현
1. `tool_definitions_collector.py` - MCP_TOOLS 로딩(현재 generator의 AST loader 재사용)
2. `internal_args_collector.py` - internal args 로딩 + defaults 보강(현재 generator 로직 재사용)
3. `service_scanner_collector.py` - 기존 mcp_service_scanner.py 마이그레이션(@mcp_service signature/parameters)
4. `tool_analyzer_collector.py` - 템플릿 계약(tool.*) 생성(현재 generator의 analyze_tool_schema 이관)

### Phase 3: 레지스트리 통합
1. `registry.py` - 모든 수집기 통합 관리
2. `pydantic_models_collector.py` - BaseModel 로드/검증 + param_types 확정 (**필수**, 단 types_files 없으면 no-op)
3. `registry.to_jinja_context()` - generate_{server}_server.py에 바로 전달 가능한 context 생성 (권장)

### Phase 4: 호환성 테스트
1. 기존 generate_outlook_server.py와 연동 테스트
2. tool_editor_web.py와 연동 테스트

## 4. BaseCollector 인터페이스 설계

```python
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Literal
from pathlib import Path

DEFAULT_SKIP_PARTS = (
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    "backups",
    "tests",
    "test",
)

@dataclass(frozen=True)
class CollectorContext:
    """
    템플릿 생성에 필요한 실행 컨텍스트(서버별 설정 포함)
    - server_name: outlook/file_handler/...
    - tools_path: tool_definition_templates.py 경로
    - internal_args_path: tool_internal_args.json 경로(옵션)
    - scan_dir: @mcp_service 스캔 대상 루트(mcp_outlook, mcp_file_handler 등)
    - types_files: Pydantic 타입 파일 목록(outlook_types.py 등)
    """
    server_name: str
    tools_path: Path
    internal_args_path: Optional[Path] = None
    scan_dir: Optional[Path] = None
    types_files: list[Path] = field(default_factory=list)

    # 스캔 제외 디렉토리(기본값은 실전에서 자주 불필요한 경로 위주)
    skip_parts: tuple[str, ...] = DEFAULT_SKIP_PARTS

    # 캐싱(장기 실행 프로세스: web editor 등)에서 유효
    cache_enabled: bool = True

    # 수집 전략
    # - ast: 안전(기본값), import side-effect 없음
    # - runtime: import 실행(부작용/환경 의존), 단 동적 등록 정보 확보 가능
    # - hybrid: ast를 우선하고 runtime으로 결손 보강(권장: 제한적으로 사용)
    collect_mode: Literal["ast", "runtime", "hybrid"] = "ast"

class BaseCollector(ABC):
    """모든 수집기의 기본 추상 클래스"""

    @abstractmethod
    def collect(self, ctx: CollectorContext) -> Dict[str, Any]:
        """ctx 기반으로 메타데이터 수집(서버별/파일별/환경별)"""
        pass

    def collect_minimal(self, ctx: CollectorContext) -> Dict[str, Any]:
        """예외 상황에서 파이프라인을 살리기 위한 최소 데이터(기본: 빈 dict)"""
        return {}

    def collect_with_fallback(self, ctx: CollectorContext) -> Dict[str, Any]:
        """예외가 나더라도 최소 산출물을 반환(권장: registry에서 warnings/errors 누적)"""
        try:
            return self.collect(ctx)
        except Exception:
            return self.collect_minimal(ctx)

    @abstractmethod
    def validate(self, metadata: Dict[str, Any]) -> bool:
        """수집된 메타데이터 유효성 검증"""
        pass

    def merge(self, existing: Dict, new: Dict) -> Dict:
        """기존 메타데이터와 새 메타데이터 병합"""
        # NOTE: 템플릿 데이터는 중첩 구조가 많아서 shallow merge는 위험.
        # registry 단계에서 deep-merge + 충돌 리포트를 권장.
        return {**existing, **new}
```

### 4.1 최종 산출물(권장): Jinja Context 계약(스키마)

MCPMetaRegistry는 최종적으로 아래 구조를 제공하면 generator/템플릿과 결합이 단순해진다:

```python
{
  "server_name": "outlook",
  "tools": [
    {
      "name": "...",
      "handler": {"class": "...", "instance": "...", "module": "...", "method": "...", "getter": "..."},
      "params": {"top": {"is_required": False, "has_default": True, "default_json": "250"}, ...},
      "object_params": {"filter": {"class_name": "FilterParams", "is_optional": True, ...}, ...},
      "call_params": {"filter": {"value": "filter_params"}, "top": {"value": "args.get('top', 250)"}, ...},
      "internal_args": {"select_params": {"type": "SelectParams", "value": {...}, "original_schema": {...}}, ...},
      "service_method": "...",
      "mcp_service": "...",  # 템플릿 호환(문자열)
    }
  ],
  "services": {"GraphMailQuery": {"module": "graph_mail_query", "instance_name": "graph_mail_query"}, ...},
  "param_types": ["FilterParams", "ExcludeParams", "SelectParams", ...],
  "modules": ["graph_mail_query", ...],
  "internal_args": {...},  # 전체 dict
  "handler_instances": [{"name": "graph_mail_query", "class": "GraphMailQuery"}, ...],
}
```

### 4.2 AST vs 런타임(하이브리드) 수집 전략

기본 원칙: **템플릿 자동화는 재현 가능성이 최우선**이므로 `collect_mode="ast"`를 기본값으로 둔다.

- `ast` 모드: `scan_dir` 이하를 AST로 스캔하여 시그니처/파라미터/데코레이터 인자를 추출  
  - 장점: import 부작용 없음, CI/서버에서 안정적
  - 단점: 런타임 계산/동적 등록(조건부 decorator 등)은 반영 불가
- `runtime` 모드: `mcp_service_decorator.MCP_SERVICE_REGISTRY` 같은 런타임 레지스트리를 활용(모듈 import 필요)  
  - 장점: 실제 실행 시점의 메타데이터와 일치
  - 단점: import side-effect/환경(토큰, 네트워크, DB, OS) 의존이 커서 자동화에 리스크
- `hybrid` 모드: AST 결과를 우선하고, runtime으로 **“결손만 보강”**  
  - 권장 merge 정책: `ast`가 채운 필드는 유지하고, runtime은 누락된 필드만 채움

### 4.3 데이터 정규화 규칙(템플릿 계약)

`tool_analyzer`는 템플릿이 기대하는 아래 규칙을 명시적으로 구현해야 한다.

1) `params` vs `object_params`
- `inputSchema.properties[param].type == "object"` 이고 `baseModel`을 확정할 수 있으면 `object_params`로 분류  
  - `call_params[param].value = f"{param}_params"`
- 그 외(`string/integer/number/boolean/array/object but baseModel unknown`)는 `params`로 분류  
  - `call_params[param].value = param`

2) required/default 우선순위
- `is_required`: `param in inputSchema.required` 기준(템플릿의 args 파싱 로직과 일치)
- `default`(값): `inputSchema.properties[param].default`가 있으면 최우선, 없으면 `mcp_service.parameters`(AST) default 사용
- `default_json`: 템플릿 코드 생성을 위한 Python literal 변환(`None/True/False` 보장)

3) handler 추출 우선순위(권장)
- (1) tool에 `handler`가 명시되어 있으면 최우선(완전 override)
- (2) tool에 `mcp_service`가 있으면 `handler.method`는 `mcp_service.name`(dict) 또는 `mcp_service`(str)
- (3) server별 기본 매핑(예: outlook → `GraphMailQuery/graph_mail_query/graph_mail_query`)
- (4) 마지막 수단: tool 이름 기반 휴리스틱/특수 케이스(가능하면 제거)

4) internal_args 처리
- `tool.internal_args = internal_args[tool.name]`(없으면 `{}`)
- internal args는 MCP 공개 signature에 노출되지 않도록 `inputSchema.properties`에서 제거(웹 에디터의 `prune_internal_properties`와 일관)
- 단, 서비스 호출에는 전달되어야 하므로 `call_params`에 `{arg}.value = f"{arg}_params"`를 추가(기존 schema param과 충돌 시 override 금지)

### 4.4 캐싱 메커니즘(구체화 + 리스크)

캐싱은 web editor처럼 장기 실행 프로세스에서 이점이 크다. 다만 **TTL만으로는 파일 변경을 놓칠 수** 있으므로 아래가 안전하다:

- cache key(권장): `server_name` + `tools_path 내용/mtime` + `internal_args 내용/mtime` + `types_files 내용/mtime` + `scan_dir 스캔 결과 fingerprint`
- TTL은 보조 수단(“영원히 stale 방지”), 무효화의 주 수단은 fingerprint/mtime 기반

`functools.lru_cache`는 TTL을 지원하지 않으므로, TTL이 필요하면 명시적 캐시 dict를 사용한다:

```python
@dataclass
class CacheEntry:
    value: dict
    created_at: float
    fingerprint: str
```

## 5. 기존 코드 호환성 유지 방안

### 5.1 Import 경로 리디렉션
```python
# mcp_editor/mcp_service_scanner.py (호환성 래퍼 예시)
# NOTE: 실제 패키지 경로는 최종 디렉토리/패키징 결정에 맞춰 확정
from mcp_editor.mcp_meta_registry.collectors import ServiceScanner, CollectorContext

# 기존 함수 시그니처 유지
def scan_mcp_decorators(file_path):
    ctx = CollectorContext(
        server_name="outlook",
        tools_path=Path("mcp_editor/outlook/tool_definition_templates.py"),
        scan_dir=Path(file_path).parent,
        types_files=[Path("mcp_outlook/outlook_types.py")],
    )
    return ServiceScanner().collect(ctx)
```

### 5.2 데이터 구조 호환성
- **handler 딕셔너리**: 기존 구조 그대로 유지
```python
{
    'handler': {
        'method': 'query_filter',
        'class': 'GraphMailQuery',
        'instance': 'graph_mail_query',
        'module': 'graph_mail_query'
    }
}
```

### 5.3 기존 템플릿 호환성
- (권장) 템플릿은 수정 없이도 동작하도록 context 계약을 맞춘다
- (현 구현) `jinja/outlook_server_template.jinja2`는 `handler_instances` 기반으로 인스턴스 getter를 자동 생성하도록 경량 리팩터링됨(legacy/registry 모두 지원)

### 5.4 generator 연동(목표에 맞춘 선택지)
- **선택지 A (가장 단순)**: `jinja/generate_{server}_server.py`가 지금처럼 MCP_TOOLS + internal_args를 읽고, registry는 **template 파일(tool_definition_templates.py / tool_internal_args.json)을 “완전한 형태”로 유지**하는 역할
- **선택지 B (가장 견고)**: generator가 registry의 `to_jinja_context()`를 호출하거나, `--config`로 context(JSON)를 받아 **휴리스틱/AST 재분석 없이 템플릿 렌더링**

## 6. 테스트 계획

### 단위 테스트
- 각 collector의 collect() 메서드 테스트
- validate() 메서드 테스트
- merge() 메서드 테스트

### 통합 테스트
1. outlook 서버 생성 테스트
2. 웹 에디터 연동 테스트
3. 프로세스 관리 테스트

### 회귀 테스트
- 기존 generate_outlook_server.py 실행 확인
- 생성된 서버 코드 diff 비교
- API 호환성 확인

## 7. 예상 문제점 및 해결방안

### 문제 1: 순환 참조
- **원인**: decorator.py와 registry.py 간 상호 참조
- **해결**: 의존성 주입 패턴 사용

### 문제 2: 기존 코드 의존성
- **원인**: 다른 스크립트들이 직접 import
- **해결**: 호환성 래퍼 제공

### 문제 3: 성능 저하
- **원인**: 추상화 레이어 추가
- **해결**: 캐싱 메커니즘 도입

### 문제 4: 템플릿이 요구하는 tool.* 구조 불일치
- **원인**: “수집(dict)”만 하고 정규화/분석(tool_analyzer)이 없거나, 스키마가 collector마다 다름
- **해결**: 최종 계약을 `to_jinja_context()`로 고정하고, generator/템플릿 기준으로 validate

### 문제 5: tool name이 Python identifier가 아닐 때
- **원인**: 템플릿이 `handle_{{ tool.name }}` 같은 형태로 코드를 생성
- **해결**: (1) tool name 정책을 제한하거나, (2) tool마다 `python_name`(slug) 필드를 만들어 템플릿에서 사용

## 8. 완료 기준

✅ 모든 collector 클래스 구현 완료
✅ BaseCollector 인터페이스 구현
✅ 기존 코드와 100% 호환
✅ 단위 테스트 커버리지 80% 이상
✅ 문서화 완료

## 9. 예상 소요 시간

- Phase 1: 30분 (기본 구조)
- Phase 2: 2시간 (수집기 구현)
- Phase 3: 1시간 (레지스트리 통합)
- Phase 4: 1시간 (테스트)
- **총 예상 시간**: 약 4-5시간
