# AST를 통한 데코레이터 함수 객체 추출 가능성 검토 보고서

## 요약

Python의 AST(Abstract Syntax Tree)를 사용하여 `@mcp_service` 데코레이터가 적용된 함수에서 사용하는 객체들을 성공적으로 추출할 수 있음을 확인했습니다.

## ✅ AST로 추출 가능한 항목들

### 1. 함수 메타데이터
- **함수 시그니처**: 파라미터 이름, 타입 힌트, 기본값
- **데코레이터 메타데이터**: tool_name, server_name, category, tags, priority, description 등
- **함수 속성**: 비동기 여부(async), 위치(line number)

### 2. 사용된 객체들

#### 2.1 변수 및 속성
- **변수명**: 함수 내에서 사용된 모든 변수 이름
- **self 속성**: `self.api_client`, `self.cache` 등 인스턴스 속성
- **모듈 속성**: `datetime.now`, `json.dumps` 등 모듈 레벨 속성

#### 2.2 함수 호출
- **일반 함수 호출**: `len()`, `sorted()`, `print()` 등
- **메소드 호출**: `self._get_access_token()`, `client.fetch_emails()` 등
- **비동기 호출**: `await` 키워드로 호출되는 모든 함수

#### 2.3 예외 처리
- **예외 타입**: `ConnectionError`, `json.JSONDecodeError` 등 catch되는 예외들

#### 2.4 기타
- **컨텍스트 매니저**: `with` 문에서 사용되는 객체
- **상수 값**: 문자열, 숫자, boolean 등 리터럴 값
- **import 문**: 파일 레벨의 import 구문

## 실제 코드베이스 분석 결과

`mcp_outlook/graph_mail_query.py` 파일의 `@mcp_service` 함수들 분석:

### GraphMailQuery.query_filter
```python
# 추출된 메타데이터
tool_name: "Handle_query_filter"
server_name: "outlook"
category: "outlook_mail"

# 추출된 self 메소드 호출
- self._build_query_url()
- self._fetch_parallel_with_url()
- self._get_access_token()

# 추출된 외부 함수 호출
- build_exclude_query()
- build_filter_query()
```

### GraphMailQuery.query_search
```python
# 추출된 비동기 호출
- await response.json()
- await response.text()
- await self._get_access_token()

# 추출된 모듈 사용
- aiohttp.ClientSession
- session.get()

# 추출된 예외 처리
- Exception
```

## ⚠️ AST 추출의 제한사항

### 1. 정적 분석의 한계
- **런타임 동적 생성 객체**: 실행 시점에 동적으로 생성되는 객체는 파악 불가
- **타입 추론**: 실제 객체의 타입은 정적으로 완벽하게 추론 불가능
- **외부 모듈 내부**: import된 외부 모듈의 내부 구조는 해당 모듈을 별도로 분석해야 함

### 2. 복잡한 패턴 처리
- **데코레이터 체인**: 여러 데코레이터가 중첩된 경우 복잡도 증가
- **메타프로그래밍**: exec, eval 등으로 생성된 코드는 분석 불가
- **동적 속성**: `getattr()`, `setattr()` 등으로 접근하는 속성은 추적 어려움

### 3. 컨텍스트 정보 부족
- **변수 스코프**: 전역 변수와 지역 변수의 구분이 추가 분석 필요
- **상속 관계**: 클래스 상속 체인의 메소드는 별도 추적 필요
- **의존성 그래프**: 함수 간 호출 관계는 전체 코드베이스 분석 필요

## 활용 방안

### 1. 코드 문서화 자동화
- 함수가 사용하는 의존성 자동 문서화
- API 엔드포인트와 내부 구현 연결 매핑

### 2. 리팩토링 지원
- 사용되지 않는 import 감지
- 메소드 이름 변경 시 영향 범위 파악

### 3. 보안 감사
- 민감한 메소드 호출 추적 (예: 파일 시스템 접근)
- 예외 처리 누락 감지

### 4. 테스트 생성
- 함수가 사용하는 mock 객체 자동 식별
- 필요한 fixture 목록 생성

## 구현 코드 예시

```python
class ObjectExtractor(ast.NodeVisitor):
    def visit_Attribute(self, node):
        """속성 접근 추출"""
        if isinstance(current, ast.Name) and current.id == 'self':
            self.used_objects['attributes'].add(full_attr)

    def visit_Await(self, node):
        """비동기 호출 추출"""
        if isinstance(node.value, ast.Call):
            self.used_objects['await_calls'].add(func_name)
```

## 결론

AST를 통한 데코레이터 함수의 객체 추출은 **대부분의 일반적인 사용 사례에서 매우 효과적**입니다. 특히 다음과 같은 정보를 높은 정확도로 추출 가능합니다:

1. ✅ 함수 시그니처와 데코레이터 메타데이터
2. ✅ self 속성 및 메소드 호출
3. ✅ 외부 함수 및 모듈 사용
4. ✅ 비동기 호출 패턴
5. ✅ 예외 처리 구조

다만 런타임 동적 행동이나 복잡한 메타프로그래밍 패턴에는 한계가 있으므로, 이러한 경우 추가적인 런타임 분석이나 다른 접근 방법을 병행해야 합니다.