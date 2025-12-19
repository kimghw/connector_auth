# MCPMetaRegistry 구축 상세 계획

## 📊 현재 상황 분석

### 디렉토리 구조 문제점
```
mcp_editor/
├── 핵심 스크립트들이 루트에 흩어짐
├── backups/ (불필요)
├── __pycache__/ (불필요)
├── outlook/ 와 file_handler/ (서버별 분리)
├── static/ 와 templates/ (Web UI)
└── 여러 .json, .backup 파일들 (정리 필요)
```

### 파일 분류

#### 1. 메타데이터 수집 관련 (MCPMetaRegistry로 통합)
- `mcp_service_scanner.py` - AST로 데코레이터 스캔
- `mcp_service_decorator.py` - 데코레이터 정의 및 레지스트리
- `extract_types.py` - 타입 정의 추출
- `pydantic_to_schema.py` - Pydantic → JSON Schema 변환

#### 2. 프로세스 관리
- `mcp_server_manager.py` - 서버 프로세스 관리

#### 3. Web UI
- `tool_editor_web.py` - 메인 Web 서버
- `static/` - 정적 파일
- `templates/` - HTML 템플릿

#### 4. CLI 도구
- `cli_regenerate_tools.py` - Tool 재생성
- `cli_extract_mcp_services.py` - 서비스 추출
- `run_tool_editor.sh` - 실행 스크립트

#### 5. 서버별 디렉토리
- `outlook/` - Outlook 서버 관련
- `file_handler/` - File Handler 서버 관련

## 🎯 목표 구조

```
mcp_editor/
├── mcp_meta_registry/              # 핵심 MCPMetaRegistry 패키지
│   ├── __init__.py
│   ├── registry.py                 # 메인 MCPMetaRegistry 클래스
│   │
│   ├── collectors/                 # 메타데이터 수집
│   │   ├── __init__.py
│   │   ├── base.py                # BaseCollector 추상 클래스
│   │   ├── decorator.py           # 데코레이터 메타데이터 수집
│   │   ├── ast_scanner.py         # AST 기반 메타데이터 수집
│   │   ├── type_extractor.py      # 타입 정의 추출
│   │   └── schema_converter.py    # Pydantic → Schema 변환
│   │
│   ├── analyzers/                  # 메타데이터 분석
│   │   ├── __init__.py
│   │   ├── service_analyzer.py    # 서비스 구조 분석
│   │   ├── signature_analyzer.py  # 함수 시그니처 분석
│   │   ├── consistency_checker.py # 일관성 검증
│   │   └── dependency_resolver.py # 의존성 분석
│   │
│   ├── generators/                 # 코드 생성
│   │   ├── __init__.py
│   │   ├── base.py                # BaseGenerator 추상 클래스
│   │   ├── server_generator.py    # 서버 코드 생성
│   │   ├── tool_generator.py      # Tool 정의 생성
│   │   ├── decorator_generator.py # 데코레이터 생성
│   │   └── templates/             # Jinja2 템플릿
│   │       ├── server.jinja2
│   │       └── tool.jinja2
│   │
│   ├── process/                    # 프로세스 관리
│   │   ├── __init__.py
│   │   ├── manager.py             # 프로세스 매니저
│   │   ├── monitor.py             # 프로세스 모니터링
│   │   └── lifecycle.py           # 생명주기 관리
│   │
│   ├── models/                     # 데이터 모델
│   │   ├── __init__.py
│   │   ├── metadata.py            # 메타데이터 모델
│   │   ├── service.py             # 서비스 모델
│   │   ├── tool.py                # Tool 모델
│   │   └── signature.py           # 시그니처 모델
│   │
│   ├── cache/                      # 캐싱
│   │   ├── __init__.py
│   │   ├── file_cache.py          # 파일 기반 캐시
│   │   └── memory_cache.py        # 메모리 캐시
│   │
│   └── utils/                      # 유틸리티
│       ├── __init__.py
│       ├── file_watcher.py        # 파일 변경 감지
│       ├── validators.py          # 검증 도구
│       └── logger.py              # 로깅 설정
│
├── servers/                        # 서버별 구성
│   ├── outlook/
│   │   ├── config.json
│   │   ├── tool_definitions.py
│   │   └── internal_args.json
│   └── file_handler/
│       ├── config.json
│       └── tool_definitions.py
│
├── web/                           # Web UI
│   ├── app.py                     # Flask/FastAPI 앱
│   ├── api/
│   │   ├── __init__.py
│   │   ├── metadata.py            # 메타데이터 API
│   │   ├── tools.py               # Tool API
│   │   └── process.py             # 프로세스 API
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
│       ├── index.html
│       └── editor.html
│
├── cli/                           # CLI 도구
│   ├── __init__.py
│   ├── mcp.py                     # 통합 CLI (Click 기반)
│   ├── commands/
│   │   ├── scan.py                # mcp scan
│   │   ├── generate.py            # mcp generate
│   │   ├── serve.py               # mcp serve
│   │   └── validate.py            # mcp validate
│   └── utils.py
│
├── tests/                         # 테스트
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/                          # 문서
│   ├── README.md
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── guides/
│       ├── getting_started.md
│       └── advanced_usage.md
│
├── config/                        # 설정
│   ├── default.yaml               # 기본 설정
│   ├── development.yaml
│   └── production.yaml
│
├── scripts/                       # 스크립트
│   ├── setup.sh                   # 초기 설정
│   ├── migrate.py                 # 마이그레이션
│   └── cleanup.sh                 # 정리
│
├── .gitignore
├── requirements.txt
├── setup.py                       # 패키지 설정
└── pyproject.toml                # 현대적 Python 프로젝트 설정
```

## 🔄 마이그레이션 계획

### Phase 1: 준비 (Day 1)
1. **백업**
   - 전체 mcp_editor 디렉토리 백업
   - Git 브랜치 생성: `feature/mcp-meta-registry`

2. **프로젝트 구조 생성**
   ```bash
   # 디렉토리 구조 생성 스크립트 작성
   scripts/create_structure.sh
   ```

### Phase 2: 핵심 모듈 이동 (Day 2-3)
1. **Collectors 모듈화**
   - `mcp_service_scanner.py` → `collectors/ast_scanner.py`
   - `mcp_service_decorator.py` → `collectors/decorator.py`
   - `extract_types.py` → `collectors/type_extractor.py`
   - 공통 인터페이스 정의 (`BaseCollector`)

2. **Process 모듈화**
   - `mcp_server_manager.py` → `process/manager.py`
   - PID 관리 개선
   - 로그 관리 통합

### Phase 3: Registry 구현 (Day 4-5)
1. **MCPMetaRegistry 클래스**
   ```python
   class MCPMetaRegistry:
       def __init__(self, config=None):
           self.collectors = {}
           self.analyzers = {}
           self.generators = {}
           self.cache = {}
           self.metadata = {}
   ```

2. **통합 인터페이스**
   - 플러그인 방식으로 collector/analyzer/generator 등록
   - 이벤트 시스템 구현
   - 캐싱 전략 구현

### Phase 4: Web UI 개선 (Day 6-7)
1. **API 분리**
   - RESTful API 설계
   - GraphQL 고려
   - WebSocket 지원

2. **프론트엔드 개선**
   - React/Vue 도입 고려
   - 실시간 업데이트
   - 더 나은 에디터 (Monaco Editor)

### Phase 5: CLI 통합 (Day 8)
1. **통합 CLI 도구**
   ```bash
   mcp scan --directory /path
   mcp generate server --name outlook
   mcp serve --port 8080
   mcp validate --file tool.json
   ```

2. **Click 프레임워크 사용**
   - 서브커맨드 구조
   - 자동 완성 지원
   - 풍부한 도움말

### Phase 6: 테스트 및 문서화 (Day 9-10)
1. **테스트 작성**
   - 단위 테스트
   - 통합 테스트
   - E2E 테스트

2. **문서 작성**
   - API 문서 (Sphinx/MkDocs)
   - 사용자 가이드
   - 개발자 가이드

## 📦 패키지 관리

### setup.py 예시
```python
setup(
    name="mcp-meta-registry",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mcp=mcp_editor.cli.mcp:main',
        ],
    },
    install_requires=[
        'fastapi',
        'jinja2',
        'click',
        'pydantic',
        'psutil',
    ],
)
```

### 의존성 관리
- `requirements.txt` - 기본 의존성
- `requirements-dev.txt` - 개발 의존성
- `requirements-web.txt` - Web UI 의존성

## 🎯 성공 지표

### 단기 (2주)
- [ ] MCPMetaRegistry 핵심 기능 구현
- [ ] 기존 기능 100% 호환
- [ ] 테스트 커버리지 80%

### 중기 (1개월)
- [ ] Web UI 개선
- [ ] CLI 도구 통합
- [ ] 문서화 완료

### 장기 (3개월)
- [ ] 플러그인 시스템
- [ ] 다중 서버 관리
- [ ] 클라우드 지원

## ⚠️ 리스크 관리

### 기술적 리스크
1. **호환성 문제**
   - 해결: 레거시 래퍼 제공
   - 점진적 마이그레이션

2. **성능 저하**
   - 해결: 적극적 캐싱
   - 비동기 처리

3. **복잡도 증가**
   - 해결: 명확한 인터페이스
   - 단계별 구현

### 프로젝트 리스크
1. **시간 부족**
   - 해결: MVP 우선
   - 단계별 릴리스

2. **테스트 부족**
   - 해결: TDD 접근
   - CI/CD 구축

## 📅 타임라인

| 주차 | 작업 내용 | 산출물 |
|------|----------|--------|
| Week 1 | 구조 생성, 핵심 모듈 이동 | 기본 패키지 구조 |
| Week 2 | Registry 구현, 통합 | MCPMetaRegistry v0.1 |
| Week 3 | Web UI, CLI 개선 | 통합 도구 |
| Week 4 | 테스트, 문서화, 배포 | v1.0 릴리스 |

---
*작성일: 2024-12-19*
*작성자: MCPMetaRegistry 설계팀*