# MCP Handler Chain Builder - 테스트 계획

## 1. 테스트 전략 개요

### 1.1 테스트 목표
- 체인 빌더의 모든 핵심 기능 검증
- 기존 MCP 시스템과의 통합 안정성 확보
- 생성된 체인 함수의 정확성 검증
- 사용자 경험 및 UI/UX 검증

### 1.2 테스트 범위
- **단위 테스트**: 개별 컴포넌트 및 함수
- **통합 테스트**: 모듈 간 상호작용
- **E2E 테스트**: 전체 워크플로우
- **성능 테스트**: 대용량 데이터 처리
- **UI/UX 테스트**: 사용자 인터페이스

## 2. 테스트 환경 구성

### 2.1 개발 환경
```yaml
Backend:
  - Python: 3.10+
  - Test Framework: pytest, pytest-asyncio
  - Coverage: pytest-cov
  - Mock: unittest.mock, pytest-mock

Frontend:
  - Node.js: 18+
  - Test Framework: Jest, React Testing Library
  - E2E: Cypress or Playwright
  - Coverage: Jest coverage

Tools:
  - CI/CD: GitHub Actions
  - Code Quality: pylint, black, ESLint
  - API Testing: Postman/Insomnia
```

### 2.2 테스트 데이터 준비
```python
# test_fixtures.py
TEST_SERVICES = {
    "mail_list": {
        "name": "mail_list",
        "parameters": [
            {"name": "folder_id", "type": "str", "required": True},
            {"name": "max_results", "type": "int", "default": 50}
        ],
        "return_type": "Dict[str, Any]"
    },
    "mail_send": {
        "name": "mail_send",
        "parameters": [
            {"name": "to", "type": "str", "required": True},
            {"name": "subject", "type": "str", "required": True},
            {"name": "body", "type": "str", "required": True}
        ],
        "return_type": "Dict[str, Any]"
    }
}
```

## 3. 백엔드 테스트 계획

### 3.1 단위 테스트

#### Test Suite 1: 서비스 스캐너
```python
# test_service_scanner.py
class TestServiceScanner:
    def test_scan_mcp_services(self):
        """@mcp_service 데코레이터가 있는 함수 탐지"""

    def test_extract_parameters(self):
        """함수 파라미터 정보 추출"""

    def test_extract_return_type(self):
        """반환 타입 정보 추출"""

    def test_handle_async_functions(self):
        """비동기 함수 처리"""
```

#### Test Suite 2: 매핑 엔진
```python
# test_mapping_engine.py
class TestMappingEngine:
    def test_direct_mapping(self):
        """직접 매핑: result.email → params.to"""

    def test_array_mapping(self):
        """배열 매핑: result.items[0].id → params.item_id"""

    def test_nested_mapping(self):
        """중첩 매핑: result.data.user.name → params.username"""

    def test_multiple_mapping(self):
        """다중 매핑: 하나의 값을 여러 파라미터로"""

    def test_duplicate_parameter_detection(self):
        """중복 파라미터 감지 및 처리"""

    def test_mapping_priority(self):
        """매핑 우선순위: 함수1 반환값 > 사용자 입력 > 기본값"""
```

#### Test Suite 3: 코드 생성
```python
# test_code_generator.py
class TestCodeGenerator:
    def test_generate_chain_function(self):
        """체인 함수 코드 생성"""

    def test_apply_decorator(self):
        """@mcp_service 데코레이터 적용"""

    def test_parameter_signature(self):
        """통합 파라미터 시그니처 생성"""

    def test_import_statements(self):
        """필요한 import 문 생성"""

    async def test_async_chain_generation(self):
        """비동기 체인 함수 생성"""
```

#### Test Suite 4: AST 파일 수정
```python
# test_ast_modifier.py
class TestASTModifier:
    def test_parse_existing_file(self):
        """기존 서비스 파일 파싱"""

    def test_insert_function(self):
        """새 함수를 파일에 삽입"""

    def test_preserve_existing_code(self):
        """기존 코드 보존 확인"""

    def test_backup_creation(self):
        """백업 파일 생성 확인"""

    def test_rollback_on_error(self):
        """에러 시 롤백 메커니즘"""
```

### 3.2 통합 테스트

#### Test Suite 5: API 통합
```python
# test_api_integration.py
class TestAPIIntegration:
    async def test_create_chain_workflow(self):
        """전체 체인 생성 워크플로우"""
        # 1. 서비스 목록 조회
        # 2. 체인 설정 생성
        # 3. 매핑 규칙 설정
        # 4. 코드 생성
        # 5. 파일 수정

    async def test_execute_chain(self):
        """생성된 체인 실행"""

    async def test_intermediate_interface(self):
        """중간 인터페이스 동작"""
```

### 3.3 엔드투엔드 테스트

```python
# test_e2e_scenarios.py
class TestE2EScenarios:
    async def test_mail_workflow_chain(self):
        """메일 워크플로우 체인 생성 및 실행"""
        # 시나리오: mail_list → mail_send

    async def test_complex_chain(self):
        """3개 이상 함수 체인"""

    async def test_error_handling_chain(self):
        """에러 처리가 포함된 체인"""
```

## 4. 프론트엔드 테스트 계획

### 4.1 컴포넌트 테스트

```javascript
// __tests__/components/FlowEditor.test.jsx
describe('FlowEditor Component', () => {
  test('renders service nodes correctly', () => {});
  test('allows drag and drop of nodes', () => {});
  test('creates edges between nodes', () => {});
  test('validates node connections', () => {});
});

// __tests__/components/ParameterMapper.test.jsx
describe('ParameterMapper Component', () => {
  test('displays source and target panels', () => {});
  test('allows drag and drop mapping', () => {});
  test('shows mapping visualization', () => {});
  test('validates type compatibility', () => {});
});
```

### 4.2 Redux 스토어 테스트

```javascript
// __tests__/store/chainSlice.test.js
describe('Chain Redux Slice', () => {
  test('adds service to chain', () => {});
  test('removes service from chain', () => {});
  test('updates mapping rules', () => {});
  test('handles duplicate parameters', () => {});
});
```

### 4.3 E2E UI 테스트 (Cypress)

```javascript
// cypress/e2e/chain_builder.cy.js
describe('Chain Builder E2E', () => {
  it('creates a simple two-function chain', () => {
    cy.visit('/builder');

    // 서비스 추가
    cy.dragService('mail_list').to('.canvas');
    cy.dragService('mail_send').to('.canvas');

    // 연결
    cy.connectNodes('mail_list', 'mail_send');

    // 매핑 설정
    cy.openMappingPanel();
    cy.mapField('mail_id', 'reference_id');

    // 생성
    cy.click('[data-testid="generate-button"]');
    cy.contains('Chain created successfully');
  });
});
```

## 5. 성능 테스트

### 5.1 부하 테스트
```python
# test_performance.py
class TestPerformance:
    def test_large_service_list(self):
        """100+ 서비스 목록 처리"""

    def test_complex_mapping(self):
        """50+ 필드 매핑 성능"""

    def test_concurrent_chain_execution(self):
        """동시 체인 실행 (10+ 동시)"""
```

### 5.2 성능 기준
- API 응답 시간: < 200ms
- UI 렌더링: < 100ms
- 체인 생성: < 1초
- 파일 수정: < 500ms

## 6. 보안 테스트

### 6.1 입력 검증
```python
# test_security.py
class TestSecurity:
    def test_sql_injection_prevention(self):
        """SQL 인젝션 방지"""

    def test_code_injection_prevention(self):
        """코드 인젝션 방지"""

    def test_xss_prevention(self):
        """XSS 공격 방지"""

    def test_path_traversal_prevention(self):
        """경로 탐색 공격 방지"""
```

## 7. 테스트 시나리오

### 7.1 Happy Path 시나리오
1. **기본 체인 생성**
   - 2개 서비스 선택
   - 단순 매핑 설정
   - 코드 생성 및 실행

2. **복잡한 체인 생성**
   - 3개 이상 서비스
   - 중복 파라미터 처리
   - 조건부 매핑

### 7.2 Edge Case 시나리오
1. **빈 체인 처리**
2. **순환 참조 감지**
3. **타입 불일치 처리**
4. **필수 파라미터 누락**

### 7.3 Error 시나리오
1. **서비스 파일 접근 불가**
2. **코드 생성 실패**
3. **네트워크 오류**
4. **동시성 충돌**

## 8. 회귀 테스트

### 8.1 자동화된 회귀 테스트
```bash
# 전체 테스트 스위트 실행
pytest tests/ --cov=mcp_builder --cov-report=html
npm test -- --coverage

# 회귀 테스트만 실행
pytest -m regression
npm run test:regression
```

### 8.2 수동 회귀 테스트 체크리스트
- [ ] 기존 서비스 파일 무결성
- [ ] 생성된 체인 함수 실행
- [ ] UI 반응성 및 사용성
- [ ] 데이터 매핑 정확성

## 9. 테스트 일정

| 주차 | 테스트 활동 | 담당 |
|------|------------|------|
| Week 1 | 단위 테스트 작성 (백엔드) | 백엔드 개발자 |
| Week 2 | 통합 테스트 구현 | 풀스택 개발자 |
| Week 3 | UI 컴포넌트 테스트 | 프론트엔드 개발자 |
| Week 4 | E2E 테스트 및 성능 테스트 | QA 엔지니어 |

## 10. 테스트 커버리지 목표

- **코드 커버리지**: 80% 이상
- **브랜치 커버리지**: 70% 이상
- **E2E 시나리오**: 핵심 워크플로우 100%

## 11. 버그 추적 및 관리

### 11.1 버그 분류
- **P0 (Critical)**: 시스템 중단, 데이터 손실
- **P1 (High)**: 주요 기능 오류
- **P2 (Medium)**: 부분 기능 오류
- **P3 (Low)**: UI/UX 이슈

### 11.2 버그 리포팅 템플릿
```markdown
**Title**: [Component] Brief description
**Priority**: P0/P1/P2/P3
**Steps to Reproduce**:
1.
2.
**Expected Result**:
**Actual Result**:
**Environment**:
**Screenshots/Logs**:
```

## 12. 테스트 완료 기준

### 12.1 출시 준비 체크리스트
- [ ] 모든 P0/P1 버그 해결
- [ ] 코드 커버리지 80% 달성
- [ ] 성능 기준 충족
- [ ] 보안 테스트 통과
- [ ] 사용자 수용 테스트 완료

### 12.2 Sign-off 프로세스
1. 개발팀 리뷰
2. QA 팀 승인
3. 프로덕트 오너 최종 승인