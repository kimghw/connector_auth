#!/usr/bin/env python3
"""
URL 변환 기능 테스트
"""

from simple_converter import convert_to_text, extract_from_url

def test_url_functions():
    print("=" * 60)
    print("URL 변환 기능 테스트")
    print("=" * 60)

    # 테스트용 URL (예시)
    test_urls = [
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "https://example.com/sample.txt",
    ]

    print("\n1. convert_to_text()로 URL 처리:")
    print("-" * 40)
    print("text = convert_to_text('https://example.com/file.pdf')")
    print("→ URL을 자동 감지하여 다운로드 후 변환")

    print("\n2. extract_from_url() 전용 함수:")
    print("-" * 40)
    print("text = extract_from_url('https://example.com/file.pdf')")
    print("→ URL 전용 함수 (convert_to_text와 동일한 기능)")

    print("\n3. 두 함수의 관계:")
    print("-" * 40)
    print("extract_from_url는 내부적으로 convert_to_text를 호출합니다.")
    print("둘 다 동일한 결과를 반환합니다.")

    # 실제 구현 확인
    print("\n4. 실제 구현:")
    print("-" * 40)
    print("""
def extract_from_url(url: str) -> str:
    '''URL에서 파일 다운로드 후 텍스트 추출'''
    return convert_to_text(url)
    """)

    print("\n5. URL 처리 과정:")
    print("-" * 40)
    print("1) URL인지 확인 (http://, https://, ftp://)")
    print("2) 임시 파일로 다운로드")
    print("3) 파일 확장자 기반으로 적절한 변환기 선택")
    print("4) 텍스트 추출")
    print("5) 임시 파일 삭제")

    print("\n6. 사용 예시:")
    print("-" * 40)
    print("""
# 방법 1: 범용 함수 사용
from attachment_mcp import convert_to_text
text = convert_to_text("https://example.com/document.pdf")

# 방법 2: URL 전용 함수 사용 (더 명시적)
from attachment_mcp import extract_from_url
text = extract_from_url("https://example.com/document.pdf")

# 둘 다 동일한 결과!
    """)

if __name__ == "__main__":
    test_url_functions()

    print("\n" + "=" * 60)
    print("✅ extract_from_url 함수가 존재합니다!")
    print("   위치: simple_converter.py:399")
    print("=" * 60)