#!/usr/bin/env python3
"""
간단한 API 테스트
사용이 얼마나 쉬운지 보여주는 예제
"""

# 방법 1: 모듈에서 직접 import
from simple_converter import convert_to_text, batch_convert, is_supported

# 방법 2: 패키지로 import (권장)
# from attachment_mcp import convert_to_text, batch_convert, is_supported

def test_simple_api():
    """간단한 API 사용 예제"""

    print("=" * 60)
    print("🚀 간단한 API 테스트")
    print("=" * 60)

    # 1. 단일 파일 변환 (한 줄!)
    print("\n1️⃣ 단일 파일 변환 (한 줄 코드)")
    print("-" * 40)

    # 테스트 파일 생성
    with open("test.txt", "w", encoding="utf-8") as f:
        f.write("Hello World!\n안녕하세요!\nThis is a test file.")

    # 한 줄로 변환!
    text = convert_to_text("test.txt")
    print(f"✅ 추출된 텍스트: {text}")

    # 2. 지원 여부 확인
    print("\n2️⃣ 파일 지원 여부 확인")
    print("-" * 40)

    test_files = ["test.pdf", "test.txt", "test.docx", "test.xyz"]
    for file in test_files:
        supported = is_supported(file)
        icon = "✅" if supported else "❌"
        print(f"{icon} {file}: {'지원됨' if supported else '지원 안됨'}")

    # 3. 여러 파일 한번에 변환
    print("\n3️⃣ 여러 파일 일괄 변환")
    print("-" * 40)

    # 추가 테스트 파일 생성
    with open("test2.txt", "w", encoding="utf-8") as f:
        f.write("Second file content")

    import json
    with open("test.json", "w", encoding="utf-8") as f:
        json.dump({"name": "테스트", "value": 123}, f, ensure_ascii=False)

    # 일괄 변환 (한 줄!)
    results = batch_convert(["test.txt", "test2.txt", "test.json"])

    for filename, content in results.items():
        if not content.startswith("Error:"):
            print(f"✅ {filename}: {len(content)} 문자")
        else:
            print(f"❌ {filename}: {content}")

    # 4. PDF 테스트 (있는 경우)
    print("\n4️⃣ PDF 변환 테스트")
    print("-" * 40)

    if os.path.exists("test_minimal.pdf"):
        try:
            pdf_text = convert_to_text("test_minimal.pdf")
            print(f"✅ PDF 텍스트 추출 성공: {len(pdf_text)} 문자")
            print(f"   미리보기: {pdf_text[:100]}...")
        except Exception as e:
            print(f"❌ PDF 변환 실패: {e}")
    else:
        print("⚠️ PDF 테스트 파일이 없습니다.")

    # 5. 다양한 인코딩 테스트
    print("\n5️⃣ 다양한 인코딩 자동 감지")
    print("-" * 40)

    # CP949 인코딩 파일 생성
    with open("test_korean.txt", "w", encoding="cp949") as f:
        f.write("한글 CP949 인코딩 테스트")

    # 자동 인코딩 감지
    text = convert_to_text("test_korean.txt")  # encoding 지정 없이도 자동 감지!
    print(f"✅ CP949 파일 읽기: {text}")

    # 6. HTML 파일 테스트
    print("\n6️⃣ HTML 태그 자동 제거")
    print("-" * 40)

    with open("test.html", "w", encoding="utf-8") as f:
        f.write("""
        <html>
            <body>
                <h1>제목</h1>
                <p>본문 내용입니다.</p>
                <div>HTML 태그가 <b>자동으로</b> 제거됩니다.</div>
            </body>
        </html>
        """)

    html_text = convert_to_text("test.html")
    print(f"✅ HTML 텍스트: {html_text.strip()}")

def test_special_functions():
    """특화 함수 테스트"""

    print("\n" + "=" * 60)
    print("🎯 특화 함수 테스트")
    print("=" * 60)

    from simple_converter import quick_convert

    # quick_convert - 더 간단한 방법
    print("\n빠른 변환 (quick_convert)")
    print("-" * 40)

    # 하나 파일
    text = quick_convert("test.txt")
    print(f"단일: {text[:30]}...")

    # 여러 파일
    texts = quick_convert("test.txt", "test2.txt", "test.json")
    print(f"다중: {len(texts)}개 파일 처리")

def cleanup():
    """테스트 파일 정리"""
    import os
    test_files = [
        "test.txt", "test2.txt", "test.json", "test.html",
        "test_korean.txt"
    ]

    for file in test_files:
        if os.path.exists(file):
            os.remove(file)

    print("\n🧹 테스트 파일 정리 완료")

if __name__ == "__main__":
    import os

    try:
        # 메인 테스트
        test_simple_api()

        # 특화 함수 테스트
        test_special_functions()

        print("\n" + "=" * 60)
        print("✨ 정말 간단하죠?")
        print("=" * 60)

        print("""
사용법 요약:
------------
from attachment_mcp import convert_to_text

# 그냥 이렇게만 하면 끝!
text = convert_to_text("any_file.pdf")
text = convert_to_text("document.docx")
text = convert_to_text("https://example.com/file.pdf")

# 여러 파일?
texts = batch_convert(["file1.pdf", "file2.txt"])

# 더 간단하게?
from attachment_mcp import quick_convert
text = quick_convert("file.pdf")
        """)

    finally:
        # 정리
        cleanup()