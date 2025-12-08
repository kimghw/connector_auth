#!/usr/bin/env python3
"""
간단한 PDF 테스트 파일 생성 스크립트
ReportLab이 설치되어 있지 않으면 텍스트 기반 PDF 시뮬레이션
"""

import os
import sys

def create_simple_pdf_with_reportlab():
    """ReportLab을 사용한 PDF 생성"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # PDF 생성
        pdf_path = "test_document.pdf"
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4

        # 제목
        c.setFont("Helvetica-Bold", 20)
        c.drawString(100, height - 100, "Test PDF Document")

        # 본문
        c.setFont("Helvetica", 12)
        y_position = height - 150

        text_lines = [
            "This is a test PDF document created for testing purposes.",
            "It contains multiple lines of text.",
            "The document includes both English and Korean text.",
            "",
            "한글 텍스트 테스트입니다.",
            "PDF 변환이 제대로 작동하는지 확인하기 위한 문서입니다.",
            "",
            "Key Features:",
            "- Text extraction testing",
            "- Multi-language support",
            "- PDF parsing capability",
            "",
            "This document was created using ReportLab library.",
            "Date: 2024-12-07"
        ]

        for line in text_lines:
            c.drawString(100, y_position, line)
            y_position -= 20

        # 페이지 저장
        c.showPage()

        # 두 번째 페이지 추가
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "Page 2 - Additional Content")

        c.setFont("Helvetica", 12)
        y_position = height - 150

        page2_lines = [
            "This is the second page of the test document.",
            "It demonstrates multi-page PDF handling.",
            "",
            "Technical Information:",
            "- Format: PDF 1.4",
            "- Pages: 2",
            "- Creator: ReportLab",
            "",
            "End of document."
        ]

        for line in page2_lines:
            c.drawString(100, y_position, line)
            y_position -= 20

        c.save()

        print(f"✅ PDF 생성 완료: {pdf_path}")
        print(f"   크기: {os.path.getsize(pdf_path):,} bytes")
        return pdf_path

    except ImportError:
        print("❌ ReportLab이 설치되지 않았습니다.")
        return None

def create_minimal_pdf():
    """최소한의 PDF 구조 생성 (라이브러리 없이)"""
    pdf_path = "test_minimal.pdf"

    # 최소한의 PDF 구조
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>
endobj
5 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Document) Tj
0 -20 Td
(This is a minimal PDF created without libraries.) Tj
0 -20 Td
(It contains simple text for testing purposes.) Tj
0 -20 Td
(Korean text cannot be displayed in this minimal version.) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
0000000312 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
565
%%EOF"""

    with open(pdf_path, 'wb') as f:
        f.write(pdf_content)

    print(f"✅ 최소 PDF 생성 완료: {pdf_path}")
    print(f"   크기: {os.path.getsize(pdf_path):,} bytes")
    return pdf_path

def main():
    print("PDF 테스트 파일 생성")
    print("=" * 50)

    # ReportLab으로 시도
    pdf_path = create_simple_pdf_with_reportlab()

    if not pdf_path:
        # 실패 시 최소 PDF 생성
        print("\n대체 방법으로 최소 PDF 생성 중...")
        pdf_path = create_minimal_pdf()

    print("\n생성된 PDF 파일:")
    print(f"  - {pdf_path}")

    if os.path.exists("test_document.pdf"):
        print("  - test_document.pdf")
    if os.path.exists("test_minimal.pdf"):
        print("  - test_minimal.pdf")

if __name__ == "__main__":
    main()