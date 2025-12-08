#!/usr/bin/env python3
"""
PDF 변환 테스트 스크립트
"""
import os
from attachment_converter import UnifiedAttachmentConverter, AttachmentAPI

def test_pdf_conversion():
    """PDF 파일 변환 테스트"""

    print("=" * 60)
    print("PDF 변환 테스트")
    print("=" * 60)

    # PDF 파일 확인
    pdf_files = ["test_minimal.pdf", "test_document.pdf"]
    available_pdfs = [f for f in pdf_files if os.path.exists(f)]

    if not available_pdfs:
        print("❌ 테스트할 PDF 파일이 없습니다.")
        print("   먼저 create_test_pdf.py를 실행하세요.")
        return

    print(f"\n발견된 PDF 파일: {', '.join(available_pdfs)}\n")

    # 1. UnifiedAttachmentConverter 테스트
    print("1. UnifiedAttachmentConverter 테스트")
    print("-" * 40)

    converter = UnifiedAttachmentConverter(enable_ocr=False)

    for pdf_file in available_pdfs:
        print(f"\n📄 파일: {pdf_file}")
        print(f"   크기: {os.path.getsize(pdf_file):,} bytes")

        result = converter.convert(pdf_file)

        if result["status"] == "success":
            print(f"✅ 변환 성공!")
            print(f"   - 방법: {result.get('method', 'unknown')}")
            print(f"   - 텍스트 길이: {len(result.get('text', ''))} 문자")

            text = result.get('text', '')
            if text:
                # 첫 200자 출력
                preview = text[:200].replace('\n', ' ')
                print(f"   - 미리보기: {preview}...")
            else:
                print("   - ⚠️ 추출된 텍스트가 없습니다.")

            # 메타데이터
            if result.get('metadata'):
                print(f"   - 메타데이터:")
                for key, value in result['metadata'].items():
                    if value:
                        print(f"     • {key}: {value}")

            # 페이지 정보
            if result.get('pages'):
                print(f"   - 페이지 수: {result['pages']}")

        else:
            print(f"❌ 변환 실패: {result.get('error', 'Unknown error')}")

    # 2. AttachmentAPI 테스트
    print("\n\n2. AttachmentAPI 간단 인터페이스 테스트")
    print("-" * 40)

    api = AttachmentAPI()

    for pdf_file in available_pdfs:
        print(f"\n📄 {pdf_file}:")

        try:
            # 간단한 텍스트 추출
            text = api.convert_to_text(pdf_file)
            if text:
                print(f"✅ 텍스트 추출 성공: {len(text)} 문자")
                print(f"   처음 100자: {text[:100]}...")
            else:
                print("⚠️ 텍스트가 비어있습니다.")

        except Exception as e:
            print(f"❌ API 호출 실패: {e}")

    # 3. 지원 포맷 확인
    print("\n\n3. PDF 지원 상태")
    print("-" * 40)

    formats = api.get_supported_formats()
    if ".pdf" in formats.get("pdf", []):
        print("✅ PDF 형식이 지원됩니다.")
    else:
        print("❌ PDF 라이브러리가 설치되지 않아 PDF를 지원하지 않습니다.")
        print("\n설치 권장 라이브러리:")
        print("  pip install pymupdf        # 가장 강력")
        print("  pip install pdfplumber     # 테이블 처리")
        print("  pip install pypdf          # 기본 추출")

def test_with_external_pdf():
    """외부 PDF 파일 테스트 (있는 경우)"""

    print("\n\n" + "=" * 60)
    print("외부 PDF 파일 검색")
    print("=" * 60)

    # 현재 디렉토리의 모든 PDF 파일 찾기
    import glob
    all_pdfs = glob.glob("*.pdf")

    if all_pdfs:
        print(f"\n발견된 PDF 파일 ({len(all_pdfs)}개):")
        for pdf in all_pdfs:
            size = os.path.getsize(pdf)
            print(f"  - {pdf}: {size:,} bytes")

        # 가장 큰 PDF 파일 테스트
        largest_pdf = max(all_pdfs, key=os.path.getsize)
        print(f"\n가장 큰 파일 테스트: {largest_pdf}")

        converter = UnifiedAttachmentConverter()
        result = converter.convert(largest_pdf)

        if result["status"] == "success":
            print(f"✅ 성공: {len(result.get('text', ''))} 문자 추출")
        else:
            print(f"❌ 실패: {result.get('error')}")
    else:
        print("현재 디렉토리에 PDF 파일이 없습니다.")

if __name__ == "__main__":
    try:
        # 메인 테스트
        test_pdf_conversion()

        # 추가 PDF 파일 테스트
        test_with_external_pdf()

        print("\n" + "=" * 60)
        print("✅ PDF 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()