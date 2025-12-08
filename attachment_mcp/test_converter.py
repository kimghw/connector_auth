#!/usr/bin/env python3
"""
첨부파일 변환기 테스트 스크립트
"""
import os
import sys
import json
from pathlib import Path
from attachment_converter import UnifiedAttachmentConverter, AttachmentAPI

def create_test_files():
    """테스트용 파일 생성"""
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)

    # 1. 텍스트 파일 생성
    text_file = test_dir / "sample.txt"
    text_file.write_text("""This is a sample text file.
It contains multiple lines.
테스트용 한글 텍스트도 포함되어 있습니다.
This file is used for testing the attachment converter.""", encoding="utf-8")

    # 2. HTML 파일 생성
    html_file = test_dir / "sample.html"
    html_file.write_text("""<!DOCTYPE html>
<html>
<head><title>Test HTML</title></head>
<body>
    <h1>Test Document</h1>
    <p>This is a <strong>test</strong> HTML document.</p>
    <p>한글 내용도 포함되어 있습니다.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
</body>
</html>""", encoding="utf-8")

    # 3. JSON 파일 생성
    json_file = test_dir / "sample.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "title": "Test JSON",
            "content": "This is a test JSON file",
            "한글키": "한글 값 테스트",
            "nested": {
                "key1": "value1",
                "key2": ["item1", "item2"]
            }
        }, f, ensure_ascii=False, indent=2)

    # 4. CSV 파일 생성
    csv_file = test_dir / "sample.csv"
    csv_file.write_text("""Name,Age,City,Country
John Doe,30,New York,USA
김철수,25,서울,대한민국
Jane Smith,28,London,UK
이영희,32,부산,대한민국""", encoding="utf-8")

    # 5. 마크다운 파일 생성
    md_file = test_dir / "sample.md"
    md_file.write_text("""# Test Markdown Document

## Introduction
This is a **test** markdown document with *various* formatting.

### Features
- Bullet point 1
- Bullet point 2
- 한글 불릿 포인트

### Code Example
```python
def hello():
    print("Hello, World!")
```

> This is a blockquote
> 한글 인용문도 테스트합니다.""", encoding="utf-8")

    return test_dir

def test_unified_converter():
    """UnifiedAttachmentConverter 테스트"""
    print("=" * 60)
    print("UnifiedAttachmentConverter 테스트")
    print("=" * 60)

    # 테스트 파일 생성
    test_dir = create_test_files()
    converter = UnifiedAttachmentConverter()

    # 각 파일 테스트
    test_files = list(test_dir.glob("*"))

    for file_path in test_files:
        print(f"\n📄 파일: {file_path.name}")
        print("-" * 40)

        try:
            result = converter.convert(str(file_path))

            if result["status"] == "success":
                print(f"✅ 변환 성공!")
                print(f"   - 파일 타입: {result.get('file_type', 'unknown')}")
                print(f"   - 변환 방법: {result.get('method', 'N/A')}")
                print(f"   - 텍스트 길이: {len(result['text'])} 문자")

                # 첫 200자만 출력
                preview = result['text'][:200].replace('\n', ' ')
                print(f"   - 미리보기: {preview}...")

                # 메타데이터가 있으면 출력
                if 'metadata' in result:
                    print(f"   - 메타데이터: {result['metadata']}")
            else:
                print(f"❌ 변환 실패: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ 예외 발생: {str(e)}")

    print("\n" + "=" * 60)

def test_attachment_api():
    """AttachmentAPI 간단한 인터페이스 테스트"""
    print("\n" + "=" * 60)
    print("AttachmentAPI 테스트")
    print("=" * 60)

    api = AttachmentAPI()
    test_dir = Path("test_files")

    if not test_dir.exists():
        create_test_files()

    # 간단한 API 테스트
    test_files = ["sample.txt", "sample.html", "sample.json"]

    for filename in test_files:
        file_path = test_dir / filename
        if file_path.exists():
            print(f"\n📄 {filename} 변환:")
            try:
                # 간단한 텍스트 변환
                text = api.convert_to_text(str(file_path))
                print(f"✅ 성공 - {len(text)} 문자")
                print(f"   미리보기: {text[:100]}...")
            except Exception as e:
                print(f"❌ 실패: {e}")

def test_batch_conversion():
    """여러 파일 일괄 변환 테스트"""
    print("\n" + "=" * 60)
    print("일괄 변환 테스트")
    print("=" * 60)

    converter = UnifiedAttachmentConverter()
    test_dir = Path("test_files")

    if not test_dir.exists():
        create_test_files()

    # 모든 파일 일괄 변환
    files = list(test_dir.glob("*"))
    results = converter.batch_convert([str(f) for f in files])

    # 결과 요약
    success_count = sum(1 for r in results if r["status"] == "success")
    fail_count = len(results) - success_count
    total_chars = sum(len(r.get("text", "")) for r in results if r["status"] == "success")

    print(f"\n📊 변환 결과:")
    print(f"   - 성공: {success_count}/{len(results)}")
    print(f"   - 실패: {fail_count}/{len(results)}")
    print(f"   - 총 텍스트: {total_chars} 문자")

    # 파일 타입별 통계
    file_types = {}
    for r in results:
        if r["status"] == "success":
            ft = r.get("file_type", "unknown")
            file_types[ft] = file_types.get(ft, 0) + 1

    print(f"\n📈 파일 타입별:")
    for ft, count in file_types.items():
        print(f"   - {ft}: {count}개")

def test_error_handling():
    """에러 처리 테스트"""
    print("\n" + "=" * 60)
    print("에러 처리 테스트")
    print("=" * 60)

    converter = UnifiedAttachmentConverter()

    # 1. 존재하지 않는 파일
    print("\n1️⃣ 존재하지 않는 파일:")
    result = converter.convert("non_existent_file.txt")
    print(f"   상태: {result['status']}")
    print(f"   에러: {result.get('error', 'N/A')}")

    # 2. 빈 경로
    print("\n2️⃣ 빈 경로:")
    result = converter.convert("")
    print(f"   상태: {result['status']}")
    print(f"   에러: {result.get('error', 'N/A')}")

    # 3. 지원하지 않는 확장자 파일 생성
    print("\n3️⃣ 지원하지 않는 확장자:")
    test_file = Path("test_files/unknown.xyz")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("Unknown file type content")
    result = converter.convert(str(test_file))
    print(f"   상태: {result['status']}")
    if result['status'] == 'success':
        print(f"   방법: {result.get('method', 'N/A')} (폴백 처리)")
        print(f"   텍스트: {result['text'][:50]}...")
    else:
        print(f"   에러: {result.get('error', 'N/A')}")

def cleanup_test_files():
    """테스트 파일 정리"""
    test_dir = Path("test_files")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
        print("\n🧹 테스트 파일 정리 완료")

if __name__ == "__main__":
    try:
        print("\n🚀 첨부파일 변환기 테스트 시작\n")

        # 1. UnifiedAttachmentConverter 테스트
        test_unified_converter()

        # 2. AttachmentAPI 테스트
        test_attachment_api()

        # 3. 일괄 변환 테스트
        test_batch_conversion()

        # 4. 에러 처리 테스트
        test_error_handling()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 테스트 파일 정리 (input 대신 자동 정리)
        cleanup_test_files()