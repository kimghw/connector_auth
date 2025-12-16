"""
실제 코드베이스에서 @mcp_service 데코레이터된 함수의 객체 추출 테스트
"""

import sys
import ast
from pathlib import Path
import json
from typing import Dict, List, Set, Any

# 이전에 만든 ObjectExtractor 클래스 재사용
class ObjectExtractor(ast.NodeVisitor):
    """데코레이터된 함수에서 사용되는 객체들을 추출하는 AST Visitor"""

    def __init__(self):
        self.used_objects = {
            'variables': set(),
            'attributes': set(),
            'function_calls': set(),
            'imports': set(),
            'class_names': set(),
            'module_attrs': set(),
            'constants': [],
            'async_calls': set(),
            'context_managers': set(),
            'exception_types': set(),
            'await_calls': set(),  # await 구문 추가
        }

    def visit_Name(self, node):
        """변수 이름 방문"""
        if isinstance(node.ctx, ast.Load):
            self.used_objects['variables'].add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """속성 접근 방문"""
        attr_chain = []
        current = node

        while isinstance(current, ast.Attribute):
            attr_chain.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            attr_chain.append(current.id)
            full_attr = '.'.join(reversed(attr_chain))

            if current.id == 'self':
                self.used_objects['attributes'].add(full_attr)
            else:
                self.used_objects['module_attrs'].add(full_attr)

        self.generic_visit(node)

    def visit_Call(self, node):
        """함수 호출 방문"""
        if isinstance(node.func, ast.Name):
            self.used_objects['function_calls'].add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            attr_chain = []
            current = node.func
            while isinstance(current, ast.Attribute):
                attr_chain.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                attr_chain.append(current.id)
                self.used_objects['function_calls'].add('.'.join(reversed(attr_chain)))

        self.generic_visit(node)

    def visit_Await(self, node):
        """await 구문 방문"""
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                self.used_objects['await_calls'].add(node.value.func.id)
            elif isinstance(node.value.func, ast.Attribute):
                attr = ast.unparse(node.value.func)
                self.used_objects['await_calls'].add(attr)
        self.generic_visit(node)

    def visit_Constant(self, node):
        """상수 값 방문"""
        if isinstance(node.value, (str, int, float, bool, type(None))):
            # 문자열 상수는 처음 20자만 저장
            if isinstance(node.value, str):
                const_val = node.value[:20] + '...' if len(node.value) > 20 else node.value
                self.used_objects['constants'].append(const_val)
            else:
                self.used_objects['constants'].append(node.value)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        """except 절 방문"""
        if node.type:
            if isinstance(node.type, ast.Name):
                self.used_objects['exception_types'].add(node.type.id)
            elif isinstance(node.type, ast.Attribute):
                self.used_objects['exception_types'].add(ast.unparse(node.type))
        self.generic_visit(node)


def analyze_mcp_service_function(file_path: str) -> Dict[str, Any]:
    """
    파일에서 @mcp_service 데코레이터된 함수들을 분석
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    tree = ast.parse(code)
    results = {}

    # 클래스 내부의 메소드 탐색
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # @mcp_service 데코레이터 확인
                    has_decorator = False
                    decorator_metadata = {}

                    for decorator in item.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == 'mcp_service':
                            has_decorator = True
                        elif isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name) and decorator.func.id == 'mcp_service':
                                has_decorator = True
                                # 데코레이터 메타데이터 추출
                                for keyword in decorator.keywords:
                                    if isinstance(keyword.value, ast.Constant):
                                        decorator_metadata[keyword.arg] = keyword.value.value
                                    elif isinstance(keyword.value, ast.List):
                                        values = []
                                        for element in keyword.value.elts:
                                            if isinstance(element, ast.Constant):
                                                values.append(element.value)
                                        decorator_metadata[keyword.arg] = values

                    if has_decorator:
                        # 함수 내부 객체 추출
                        extractor = ObjectExtractor()
                        extractor.visit(item)

                        # 파라미터 추출
                        params = []
                        for arg in item.args.args:
                            if arg.arg != 'self':
                                param_info = {'name': arg.arg}
                                if arg.annotation:
                                    param_info['type'] = ast.unparse(arg.annotation)
                                params.append(param_info)

                        function_key = f"{class_name}.{item.name}"
                        results[function_key] = {
                            'class': class_name,
                            'function': item.name,
                            'decorator_metadata': decorator_metadata,
                            'parameters': params,
                            'is_async': isinstance(item, ast.AsyncFunctionDef),
                            'used_objects': {
                                k: list(v) if isinstance(v, set) else v
                                for k, v in extractor.used_objects.items()
                            },
                            'line_number': item.lineno
                        }

    return results


def main():
    # graph_mail_query.py 파일 분석
    file_path = Path('mcp_outlook/graph_mail_query.py')

    if not file_path.exists():
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return

    results = analyze_mcp_service_function(str(file_path))

    print("=== 실제 코드베이스 @mcp_service 함수 분석 결과 ===\n")

    for func_name, info in results.items():
        print(f"\n🎯 {func_name} (Line {info['line_number']})")
        print(f"   클래스: {info['class']}")
        print(f"   함수: {info['function']}")
        print(f"   비동기: {info['is_async']}")

        if info['decorator_metadata']:
            print("\n   📦 데코레이터 메타데이터:")
            for key, value in info['decorator_metadata'].items():
                if isinstance(value, list):
                    value = ', '.join(value)
                print(f"      - {key}: {value}")

        if info['parameters']:
            print("\n   📝 파라미터:")
            for param in info['parameters']:
                type_str = f": {param.get('type', 'Any')}" if 'type' in param else ""
                print(f"      - {param['name']}{type_str}")

        print("\n   🔍 사용된 객체들:")
        used = info['used_objects']

        # 주요 항목만 표시
        if used.get('attributes'):
            attrs = [a for a in used['attributes'] if a.startswith('self.')]
            if attrs:
                print(f"\n      self 속성들: {', '.join(sorted(attrs)[:10])}")

        if used.get('await_calls'):
            print(f"\n      await 호출들: {', '.join(sorted(used['await_calls'])[:10])}")

        if used.get('function_calls'):
            # self 메소드 호출 필터링
            self_methods = [f for f in used['function_calls'] if f.startswith('self.')]
            other_calls = [f for f in used['function_calls'] if not f.startswith('self.')]

            if self_methods:
                print(f"\n      self 메소드 호출: {', '.join(sorted(self_methods)[:10])}")
            if other_calls:
                print(f"\n      기타 함수 호출: {', '.join(sorted(other_calls)[:10])}")

        if used.get('module_attrs'):
            # 유용한 모듈 속성만 필터링
            useful_attrs = [a for a in used['module_attrs']
                          if not a.startswith('_') and '._' not in a]
            if useful_attrs:
                print(f"\n      모듈 속성: {', '.join(sorted(useful_attrs)[:10])}")

        if used.get('exception_types'):
            print(f"\n      예외 타입: {', '.join(sorted(used['exception_types']))}")

        # 상수 요약
        if used.get('constants'):
            const_types = {}
            for const in used['constants']:
                const_type = type(const).__name__
                const_types[const_type] = const_types.get(const_type, 0) + 1
            if const_types:
                print(f"\n      상수 타입: {', '.join(f'{t}({c})' for t, c in const_types.items())}")

    # 분석 요약
    print("\n" + "="*60)
    print("\n📊 분석 요약:")
    print(f"   - 분석된 @mcp_service 함수 수: {len(results)}")

    # 공통 패턴 찾기
    all_self_attrs = set()
    all_await_calls = set()
    all_exceptions = set()

    for info in results.values():
        all_self_attrs.update(info['used_objects'].get('attributes', []))
        all_await_calls.update(info['used_objects'].get('await_calls', []))
        all_exceptions.update(info['used_objects'].get('exception_types', []))

    print(f"\n   공통 self 속성들:")
    for attr in sorted(all_self_attrs)[:10]:
        print(f"      - {attr}")

    if all_await_calls:
        print(f"\n   공통 await 호출들:")
        for call in sorted(all_await_calls)[:10]:
            print(f"      - {call}")

    if all_exceptions:
        print(f"\n   처리되는 예외들:")
        for exc in sorted(all_exceptions):
            print(f"      - {exc}")

    # JSON으로 저장
    output_file = 'real_mcp_service_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n💾 상세 분석 결과를 {output_file}에 저장했습니다.")


if __name__ == "__main__":
    main()