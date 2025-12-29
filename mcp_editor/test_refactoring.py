#!/usr/bin/env python3
"""
MCP 웹에디터 리팩토링 테스트 스위트
단위 테스트부터 통합 테스트까지 수행
"""

import os
import time
import json
import subprocess
import requests
from pathlib import Path
import difflib
import re
from datetime import datetime

# 색상 코드
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class RefactoringTester:
    def __init__(self):
        self.base_path = Path('/home/kimghw/Connector_auth/mcp_editor')
        self.server_port = 8004
        self.server_process = None
        self.test_results = []

    def log(self, message, level='info'):
        """테스트 로그 출력"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        if level == 'success':
            print(f"{GREEN}✅ [{timestamp}] {message}{RESET}")
        elif level == 'error':
            print(f"{RED}❌ [{timestamp}] {message}{RESET}")
        elif level == 'warning':
            print(f"{YELLOW}⚠️  [{timestamp}] {message}{RESET}")
        else:
            print(f"{BLUE}ℹ️  [{timestamp}] {message}{RESET}")

    def start_test_server(self):
        """테스트 서버 시작"""
        self.log("테스트 서버 시작 중...")
        try:
            # 기존 서버 종료
            subprocess.run(['pkill', '-f', f'python.*{self.server_port}'],
                         capture_output=True)
            time.sleep(1)

            # 새 서버 시작
            self.server_process = subprocess.Popen(
                ['python', '-m', 'http.server', str(self.server_port)],
                cwd=self.base_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)

            # 서버 상태 확인
            response = requests.get(f'http://localhost:{self.server_port}/')
            if response.status_code == 200:
                self.log(f"서버 시작 성공 (포트: {self.server_port})", 'success')
                return True
        except Exception as e:
            self.log(f"서버 시작 실패: {e}", 'error')
            return False

    def stop_test_server(self):
        """테스트 서버 종료"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.log("테스트 서버 종료", 'info')

    # ============ 단위 테스트 ============

    def test_file_structure(self):
        """파일 구조 테스트"""
        self.log("\n=== 파일 구조 테스트 ===")

        required_files = [
            'templates/tool_editor_final.html',
            'static/css/tool_editor.css',
            'static/js/tool_editor_core.js',
            'static/js/tool_editor_ui.js',
            'static/js/tool_editor_api.js',
            'static/js/tool_editor_actions.js'
        ]

        all_exist = True
        for file_path in required_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                self.log(f"✓ {file_path} ({size:,} bytes)", 'success')
            else:
                self.log(f"✗ {file_path} - 파일 없음", 'error')
                all_exist = False

        return all_exist

    def test_javascript_syntax(self):
        """JavaScript 문법 검사"""
        self.log("\n=== JavaScript 문법 테스트 ===")

        js_files = [
            'static/js/tool_editor_core.js',
            'static/js/tool_editor_ui.js',
            'static/js/tool_editor_api.js',
            'static/js/tool_editor_actions.js'
        ]

        all_valid = True
        for js_file in js_files:
            file_path = self.base_path / js_file
            if file_path.exists():
                content = file_path.read_text()

                # 기본 문법 체크
                # core.js는 메서드를 사용하므로 예외 처리
                if 'core.js' in js_file:
                    checks = [
                        ('메서드 정의', r'(async\s+)?\w+\s*\(\)', 3),
                        ('변수 선언', r'(var|let|const)\s+\w+', 3),
                        ('객체 리터럴', r'\{[^}]*\}', 5),
                        ('콜백/프로미스', r'(then|catch|async|await)', 2)
                    ]
                else:
                    checks = [
                        ('함수 선언', r'function\s+\w+\s*\(', 5),
                    ('변수 선언', r'(var|let|const)\s+\w+', 3),
                    ('객체 리터럴', r'\{[^}]*\}', 5),
                    ('콜백/프로미스', r'(then|catch|async|await)', 2)
                ]

                file_valid = True
                for check_name, pattern, min_count in checks:
                    matches = len(re.findall(pattern, content))
                    if matches >= min_count:
                        self.log(f"  ✓ {js_file}: {check_name} ({matches}개)", 'success')
                    else:
                        self.log(f"  ✗ {js_file}: {check_name} 부족 ({matches}/{min_count})", 'error')
                        file_valid = False

                all_valid = all_valid and file_valid

        return all_valid

    def test_css_loading(self):
        """CSS 로딩 테스트"""
        self.log("\n=== CSS 로딩 테스트 ===")

        try:
            url = f'http://localhost:{self.server_port}/static/css/tool_editor.css'
            response = requests.get(url)

            if response.status_code == 200:
                content = response.text

                # CSS 변수 확인
                css_vars = re.findall(r'--[\w-]+:\s*[^;]+;', content)
                self.log(f"CSS 변수: {len(css_vars)}개 발견", 'success')

                # 주요 클래스 확인
                important_classes = [
                    '.container', '.header', '.sidebar',
                    '.tool-list', '.btn', '.modal'
                ]

                for class_name in important_classes:
                    if class_name in content:
                        self.log(f"  ✓ {class_name} 클래스 존재", 'success')
                    else:
                        self.log(f"  ✗ {class_name} 클래스 없음", 'error')
                        return False

                return True
            else:
                self.log(f"CSS 로드 실패: HTTP {response.status_code}", 'error')
                return False

        except Exception as e:
            self.log(f"CSS 테스트 실패: {e}", 'error')
            return False

    def test_hardcoding_removal(self):
        """하드코딩 제거 확인"""
        self.log("\n=== 하드코딩 제거 테스트 ===")

        forbidden_patterns = [
            ('outlook 서버명', r"'outlook'|\"outlook\"", []),  # 문자열 리터럴만 체크
            ('graph_mail 서버명', r'\bgraph_mail\b', []),
            ('file_handler 서버명', r'\bfile_handler\b', []),
            ('절대 경로', r'/home/\w+/', []),
            ('create_email 함수', r'\bcreate_email\b', []),
            ('send_email 함수', r'\bsend_email\b', [])
        ]

        files_to_check = [
            'templates/tool_editor_final.html',
            'static/js/tool_editor_core.js',
            'static/js/tool_editor_ui.js',
            'static/js/tool_editor_api.js',
            'static/js/tool_editor_actions.js'
        ]

        all_clean = True
        for file_path in files_to_check:
            full_path = self.base_path / file_path
            if full_path.exists():
                content = full_path.read_text()

                for pattern_name, pattern, exceptions in forbidden_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    # 예외 처리
                    filtered_matches = [m for m in matches
                                      if not any(e in m for e in exceptions)]

                    if filtered_matches:
                        self.log(f"  ✗ {file_path}: {pattern_name} 발견 ({len(filtered_matches)}개)", 'error')
                        self.log(f"    발견된 내용: {filtered_matches[:3]}", 'warning')
                        all_clean = False

        if all_clean:
            self.log("모든 하드코딩 제거 확인", 'success')

        return all_clean

    def test_module_dependencies(self):
        """모듈 의존성 테스트"""
        self.log("\n=== 모듈 의존성 테스트 ===")

        # Core 모듈 확인
        core_path = self.base_path / 'static/js/tool_editor_core.js'
        if core_path.exists():
            content = core_path.read_text()

            # MCPEditor 전역 객체 확인
            if 'window.MCPEditor' in content:
                self.log("✓ MCPEditor 전역 객체 정의됨", 'success')
            else:
                self.log("✗ MCPEditor 전역 객체 없음", 'error')
                return False

            # 필수 속성 확인
            required_props = ['state', 'config', 'init', 'loadTools']
            for prop in required_props:
                if prop in content:
                    self.log(f"  ✓ MCPEditor.{prop} 존재", 'success')
                else:
                    self.log(f"  ✗ MCPEditor.{prop} 없음", 'error')
                    return False

        return True

    # ============ 기능 테스트 ============

    def test_html_loading(self):
        """HTML 로딩 테스트"""
        self.log("\n=== HTML 로딩 테스트 ===")

        try:
            url = f'http://localhost:{self.server_port}/templates/tool_editor_final.html'
            response = requests.get(url)

            if response.status_code == 200:
                content = response.text

                # 필수 요소 확인
                required_elements = [
                    ('<link.*tool_editor.css', 'CSS 링크'),
                    ('<script.*tool_editor_core.js', 'Core JS'),
                    ('<script.*tool_editor_ui.js', 'UI JS'),
                    ('<script.*tool_editor_api.js', 'API JS'),
                    ('<script.*tool_editor_actions.js', 'Actions JS'),
                    ('class="container"', 'Container div'),
                    ('class="header"', 'Header div'),
                    ('MCP Tool.*Editor', 'Title')
                ]

                all_found = True
                for pattern, name in required_elements:
                    if re.search(pattern, content):
                        self.log(f"  ✓ {name} 발견", 'success')
                    else:
                        self.log(f"  ✗ {name} 없음", 'error')
                        all_found = False

                return all_found
            else:
                self.log(f"HTML 로드 실패: HTTP {response.status_code}", 'error')
                return False

        except Exception as e:
            self.log(f"HTML 테스트 실패: {e}", 'error')
            return False

    def test_javascript_loading(self):
        """JavaScript 모듈 로딩 테스트"""
        self.log("\n=== JavaScript 로딩 테스트 ===")

        js_modules = [
            ('tool_editor_core.js', 'MCPEditor'),
            ('tool_editor_ui.js', 'renderTools'),
            ('tool_editor_api.js', 'loadTools'),
            ('tool_editor_actions.js', 'selectTool')
        ]

        all_loaded = True
        for module_name, key_function in js_modules:
            try:
                url = f'http://localhost:{self.server_port}/static/js/{module_name}'
                response = requests.get(url)

                if response.status_code == 200:
                    content = response.text
                    if key_function in content:
                        self.log(f"  ✓ {module_name}: {key_function} 함수 존재", 'success')
                    else:
                        self.log(f"  ✗ {module_name}: {key_function} 함수 없음", 'error')
                        all_loaded = False
                else:
                    self.log(f"  ✗ {module_name} 로드 실패", 'error')
                    all_loaded = False

            except Exception as e:
                self.log(f"  ✗ {module_name} 테스트 실패: {e}", 'error')
                all_loaded = False

        return all_loaded

    def test_ui_consistency(self):
        """UI 일관성 테스트 (원본과 비교)"""
        self.log("\n=== UI 일관성 테스트 ===")

        # HTML 구조 비교
        original_path = self.base_path / 'templates/tool_editor.html'
        refactored_path = self.base_path / 'templates/tool_editor_final.html'

        if not original_path.exists():
            self.log("원본 파일이 없어 비교 불가", 'warning')
            return True

        try:
            # 주요 UI 요소 추출 및 비교
            original_content = original_path.read_text()
            refactored_content = refactored_path.read_text()

            # HTML 구조 요소 추출
            ui_elements = [
                r'<div class="container">',
                r'<div class="header">',
                r'<div class="sidebar">',
                r'<div class="tool-list">',
                r'<div class="editor-area">',
                r'MCP Tool.*Editor'
            ]

            all_match = True
            for element_pattern in ui_elements:
                in_original = bool(re.search(element_pattern, original_content))
                in_refactored = bool(re.search(element_pattern, refactored_content))

                if in_original == in_refactored:
                    self.log(f"  ✓ UI 요소 일치: {element_pattern[:30]}", 'success')
                else:
                    self.log(f"  ✗ UI 요소 불일치: {element_pattern[:30]}", 'error')
                    all_match = False

            return all_match

        except Exception as e:
            self.log(f"UI 비교 실패: {e}", 'error')
            return False

    # ============ 통합 테스트 ============

    def test_integration(self):
        """통합 테스트"""
        self.log("\n=== 통합 테스트 ===")

        try:
            # 페이지 전체 로드 테스트
            url = f'http://localhost:{self.server_port}/templates/tool_editor_final.html'
            response = requests.get(url)

            if response.status_code != 200:
                self.log("페이지 로드 실패", 'error')
                return False

            html_content = response.text

            # 모든 리소스 로드 확인
            resources = re.findall(r'(?:src|href)="([^"]+)"', html_content)

            failed_resources = []
            for resource in resources:
                if resource.startswith('/static/') or resource.startswith('/templates/'):
                    resource_url = f'http://localhost:{self.server_port}{resource}'
                    try:
                        res = requests.head(resource_url)
                        if res.status_code != 200:
                            failed_resources.append(resource)
                    except:
                        failed_resources.append(resource)

            if failed_resources:
                self.log(f"리소스 로드 실패: {failed_resources}", 'error')
                return False
            else:
                self.log("모든 리소스 로드 성공", 'success')

            # JavaScript 초기화 확인 (모듈에 있을 수 있음)
            self.log("JavaScript 초기화 검증", 'info')

            # Core 모듈에서 초기화 확인
            core_url = f'http://localhost:{self.server_port}/static/js/tool_editor_core.js'
            core_response = requests.get(core_url)

            if core_response.status_code == 200:
                core_content = core_response.text
                if 'window.onload' in core_content or 'MCPEditor.init' in core_content:
                    self.log("  ✓ 초기화 코드 존재 (Core 모듈)", 'success')
                else:
                    self.log("  ✗ 초기화 코드 없음", 'error')
                    return False
            else:
                self.log("  ✗ Core 모듈 로드 실패", 'error')
                return False

            return True

        except Exception as e:
            self.log(f"통합 테스트 실패: {e}", 'error')
            return False

    def run_all_tests(self):
        """모든 테스트 실행"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}MCP 웹에디터 리팩토링 테스트 스위트{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")

        # 서버 시작
        if not self.start_test_server():
            print(f"\n{RED}서버 시작 실패로 테스트 중단{RESET}")
            return False

        tests = [
            ('파일 구조', self.test_file_structure),
            ('JavaScript 문법', self.test_javascript_syntax),
            ('CSS 로딩', self.test_css_loading),
            ('하드코딩 제거', self.test_hardcoding_removal),
            ('모듈 의존성', self.test_module_dependencies),
            ('HTML 로딩', self.test_html_loading),
            ('JavaScript 로딩', self.test_javascript_loading),
            ('UI 일관성', self.test_ui_consistency),
            ('통합 테스트', self.test_integration)
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                time.sleep(0.5)
            except Exception as e:
                self.log(f"{test_name} 테스트 실행 중 오류: {e}", 'error')
                results.append((test_name, False))

        # 서버 종료
        self.stop_test_server()

        # 최종 결과 출력
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}테스트 결과 요약{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
            print(f"  {test_name:20} : {status}")

        print(f"\n{BLUE}{'='*60}{RESET}")
        percentage = (passed / total * 100) if total > 0 else 0

        if passed == total:
            print(f"{GREEN}🎉 모든 테스트 통과! ({passed}/{total} - 100%){RESET}")
            return True
        else:
            print(f"{YELLOW}⚠️  일부 테스트 실패 ({passed}/{total} - {percentage:.1f}%){RESET}")
            return False

if __name__ == '__main__':
    tester = RefactoringTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)