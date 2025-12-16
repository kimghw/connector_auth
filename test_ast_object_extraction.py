"""
AST를 사용한 데코레이터 함수 내부 객체 추출 테스트

이 스크립트는 @mcp_service 데코레이터된 함수들이 사용하는 다양한 객체들을
AST를 통해 추출할 수 있는지 검증합니다.
"""

import ast
from typing import Dict, List, Set, Any
import json


class ObjectExtractor(ast.NodeVisitor):
    """데코레이터된 함수에서 사용되는 객체들을 추출하는 AST Visitor"""

    def __init__(self):
        self.used_objects = {
            'variables': set(),           # 변수 이름들
            'attributes': set(),           # 객체 속성 접근 (예: self.client)
            'function_calls': set(),       # 함수 호출
            'imports': set(),              # import된 모듈들
            'class_names': set(),          # 사용된 클래스 이름들
            'module_attrs': set(),         # 모듈 속성 (예: os.path)
            'constants': [],               # 상수 값들
            'async_calls': set(),          # async 함수 호출
            'context_managers': set(),     # with 문 사용 객체
            'exception_types': set(),      # except에서 잡는 예외 타입
        }

    def visit_Name(self, node):
        """변수 이름 방문"""
        if isinstance(node.ctx, ast.Load):  # 변수를 읽는 경우만
            self.used_objects['variables'].add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """속성 접근 방문 (예: self.client, module.function)"""
        attr_chain = []
        current = node

        # 속성 체인 추적 (예: self.client.get_data)
        while isinstance(current, ast.Attribute):
            attr_chain.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            attr_chain.append(current.id)
            full_attr = '.'.join(reversed(attr_chain))

            if current.id == 'self':
                # self.xxx 형태
                self.used_objects['attributes'].add(full_attr)
            else:
                # module.xxx 형태
                self.used_objects['module_attrs'].add(full_attr)

        self.generic_visit(node)

    def visit_Call(self, node):
        """함수 호출 방문"""
        if isinstance(node.func, ast.Name):
            self.used_objects['function_calls'].add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # 메소드 호출 (예: obj.method())
            attr_chain = []
            current = node.func
            while isinstance(current, ast.Attribute):
                attr_chain.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                attr_chain.append(current.id)
                self.used_objects['function_calls'].add('.'.join(reversed(attr_chain)))

        self.generic_visit(node)

    def visit_Constant(self, node):
        """상수 값 방문"""
        if isinstance(node.value, (str, int, float, bool, type(None))):
            self.used_objects['constants'].append(node.value)
        self.generic_visit(node)

    def visit_AsyncCall(self, node):
        """async 함수 호출 방문"""
        if isinstance(node, ast.Await):
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    self.used_objects['async_calls'].add(node.value.func.id)
                elif isinstance(node.value.func, ast.Attribute):
                    attr = ast.unparse(node.value.func)
                    self.used_objects['async_calls'].add(attr)
        self.generic_visit(node)

    def visit_With(self, node):
        """with 문 방문 (context manager)"""
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                if isinstance(item.context_expr.func, ast.Name):
                    self.used_objects['context_managers'].add(item.context_expr.func.id)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        """except 절 방문"""
        if node.type:
            if isinstance(node.type, ast.Name):
                self.used_objects['exception_types'].add(node.type.id)
            elif isinstance(node.type, ast.Attribute):
                self.used_objects['exception_types'].add(ast.unparse(node.type))
        self.generic_visit(node)

    def visit_Import(self, node):
        """import 문 방문"""
        for alias in node.names:
            self.used_objects['imports'].add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """from ... import 문 방문"""
        if node.module:
            for alias in node.names:
                self.used_objects['imports'].add(f"{node.module}.{alias.name}")
        self.generic_visit(node)


def extract_decorated_function_objects(code: str, decorator_name: str = "mcp_service") -> Dict[str, Any]:
    """
    데코레이터된 함수에서 사용되는 모든 객체들을 추출

    Args:
        code: 파싱할 Python 코드
        decorator_name: 찾을 데코레이터 이름

    Returns:
        함수별 사용 객체 정보
    """
    tree = ast.parse(code)
    results = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 데코레이터 체크
            has_decorator = False
            decorator_metadata = {}

            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                    has_decorator = True
                elif isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Name) and decorator.func.id == decorator_name:
                        has_decorator = True
                        # 데코레이터 인자 추출
                        for keyword in decorator.keywords:
                            if isinstance(keyword.value, ast.Constant):
                                decorator_metadata[keyword.arg] = keyword.value.value

            if has_decorator:
                # 함수 내부 객체 추출
                extractor = ObjectExtractor()
                extractor.visit(node)

                # 함수 파라미터도 추출
                params = []
                for arg in node.args.args:
                    if arg.arg != 'self':
                        param_info = {'name': arg.arg}
                        if arg.annotation:
                            param_info['type'] = ast.unparse(arg.annotation)
                        params.append(param_info)

                results[node.name] = {
                    'decorator_metadata': decorator_metadata,
                    'parameters': params,
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'used_objects': {
                        k: list(v) if isinstance(v, set) else v
                        for k, v in extractor.used_objects.items()
                    },
                    'line_number': node.lineno
                }

    return results


# 테스트 코드 예제
test_code = '''
import asyncio
from typing import Optional, List
from datetime import datetime
import json

class EmailClient:
    def __init__(self):
        self.api_client = None
        self.cache = {}

@mcp_service(
    tool_name="handle_email",
    description="Handle email operations",
    category="email",
    tags=["email", "outlook"],
    priority=1
)
async def handle_email_query(
    self,
    user_email: str,
    filter: Optional[str] = None,
    top: int = 10
) -> dict:
    """Complex function showing various object usages"""

    # 1. 인스턴스 속성 접근
    client = self.api_client
    cached_data = self.cache.get(user_email)

    # 2. 모듈 함수 호출
    current_time = datetime.now()
    json_data = json.dumps({"user": user_email})

    # 3. 조건문과 상수
    if filter == "important":
        priority = 1
        status = "high"
    else:
        priority = 0
        status = "normal"

    # 4. 예외 처리
    try:
        # 5. async 호출
        response = await client.fetch_emails(user_email, filter)

        # 6. 컨텍스트 매니저
        with open("log.txt", "w") as f:
            f.write(f"Query for {user_email}")

        # 7. 리스트 컴프리헨션과 내장 함수
        email_ids = [email["id"] for email in response["items"]]
        total = len(email_ids)
        sorted_emails = sorted(response["items"], key=lambda x: x["date"])

    except ConnectionError as e:
        print(f"Connection error: {e}")
        raise
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

    # 8. 딕셔너리 생성과 반환
    result = {
        "user": user_email,
        "count": total,
        "emails": sorted_emails[:top],
        "timestamp": current_time.isoformat(),
        "status": status
    }

    return result

@mcp_service(tool_name="send_email")
def send_email(self, to: str, subject: str, body: str) -> bool:
    """Simple sync function"""
    self.client.send(to, subject, body)
    return True
'''

# 테스트 실행
if __name__ == "__main__":
    results = extract_decorated_function_objects(test_code, "mcp_service")

    print("=== AST를 통한 데코레이터 함수 객체 추출 결과 ===\n")

    for func_name, info in results.items():
        print(f"\n📌 함수: {func_name} (Line {info['line_number']})")
        print(f"   비동기: {info['is_async']}")

        print("\n   📦 데코레이터 메타데이터:")
        for key, value in info['decorator_metadata'].items():
            print(f"      - {key}: {value}")

        print("\n   📝 파라미터:")
        for param in info['parameters']:
            type_str = f": {param.get('type', 'Any')}" if 'type' in param else ""
            print(f"      - {param['name']}{type_str}")

        print("\n   🔍 사용된 객체들:")

        used = info['used_objects']

        if used['variables']:
            print(f"\n      변수들: {', '.join(sorted(used['variables']))}")

        if used['attributes']:
            print(f"\n      self 속성들: {', '.join(sorted(used['attributes']))}")

        if used['function_calls']:
            print(f"\n      함수 호출들: {', '.join(sorted(used['function_calls']))}")

        if used['module_attrs']:
            print(f"\n      모듈 속성들: {', '.join(sorted(used['module_attrs']))}")

        if used['async_calls']:
            print(f"\n      비동기 호출들: {', '.join(sorted(used['async_calls']))}")

        if used['context_managers']:
            print(f"\n      컨텍스트 매니저들: {', '.join(sorted(used['context_managers']))}")

        if used['exception_types']:
            print(f"\n      예외 타입들: {', '.join(sorted(used['exception_types']))}")

        if used['imports']:
            print(f"\n      임포트들: {', '.join(sorted(used['imports']))}")

        # 상수는 너무 많을 수 있으므로 타입별로 요약
        const_types = {}
        for const in used['constants']:
            const_type = type(const).__name__
            const_types[const_type] = const_types.get(const_type, 0) + 1

        if const_types:
            print(f"\n      상수 타입들: {', '.join(f'{t}({c})' for t, c in const_types.items())}")

    print("\n" + "="*60)
    print("\n✅ AST 추출 가능한 항목들:")
    print("   - 함수 시그니처 (파라미터, 타입 힌트, 기본값)")
    print("   - 데코레이터 메타데이터")
    print("   - 사용된 변수명")
    print("   - self 속성 접근")
    print("   - 함수/메소드 호출")
    print("   - 모듈 속성 접근")
    print("   - 상수 값")
    print("   - 비동기 호출")
    print("   - 컨텍스트 매니저")
    print("   - 예외 타입")
    print("   - import 문")

    print("\n⚠️ AST 추출 제한사항:")
    print("   - 런타임 동적 생성 객체는 추출 불가")
    print("   - 실제 객체 타입은 추론만 가능 (정적 분석 한계)")
    print("   - 외부 모듈의 내부 구조는 파악 불가")
    print("   - 데코레이터 체인이나 복잡한 메타프로그래밍은 제한적")

    # JSON으로 저장
    with open('ast_extraction_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print("\n💾 결과를 ast_extraction_results.json 파일로 저장했습니다.")