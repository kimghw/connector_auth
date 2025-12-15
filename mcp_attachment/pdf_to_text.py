#!/usr/bin/env python3
"""
PDF to Text Converter - Advanced Version
PDF 파일을 텍스트로 변환하는 고급 유틸리티
Supports: pypdf, pdfplumber, pymupdf, pdfminer, OCR
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union
import argparse
import json
from datetime import datetime
import re
import warnings
warnings.filterwarnings('ignore')

# 최신 PDF 처리 라이브러리들
try:
    from pypdf import PdfReader  # 최신 pypdf (구 PyPDF2)
    PYPDF_AVAILABLE = True
except ImportError:
    try:
        import PyPDF2
        from PyPDF2 import PdfReader
        PYPDF_AVAILABLE = True
    except ImportError:
        PYPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF - 가장 강력한 PDF 처리
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    import pdfminer
    from pdfminer.high_level import extract_text, extract_pages
    from pdfminer.layout import LAParams, LTTextBox
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False


class AdvancedPDFConverter:
    """고급 PDF 텍스트 변환기"""

    def __init__(self, method: str = "auto", enable_ocr: bool = False):
        """
        초기화

        Args:
            method: 사용할 방법 ("auto", "pypdf", "pdfplumber", "pymupdf", "pdfminer")
            enable_ocr: OCR 사용 여부 (스캔된 PDF용)
        """
        self.method = method
        self.enable_ocr = enable_ocr
        self.available_methods = self._check_available_methods()
        self._select_method()

    def _check_available_methods(self) -> List[str]:
        """사용 가능한 방법 확인"""
        methods = []
        if PYMUPDF_AVAILABLE:
            methods.append("pymupdf")
        if PDFPLUMBER_AVAILABLE:
            methods.append("pdfplumber")
        if PDFMINER_AVAILABLE:
            methods.append("pdfminer")
        if PYPDF_AVAILABLE:
            methods.append("pypdf")
        if OCR_AVAILABLE:
            methods.append("ocr")
        return methods

    def _select_method(self):
        """최적의 방법 자동 선택"""
        if self.method == "auto":
            # 우선순위: PyMuPDF > pdfplumber > pdfminer > pypdf
            if "pymupdf" in self.available_methods:
                self.method = "pymupdf"
            elif "pdfplumber" in self.available_methods:
                self.method = "pdfplumber"
            elif "pdfminer" in self.available_methods:
                self.method = "pdfminer"
            elif "pypdf" in self.available_methods:
                self.method = "pypdf"
            else:
                raise ImportError(
                    "PDF 처리 라이브러리가 설치되지 않았습니다.\n"
                    "다음 중 하나를 설치하세요:\n"
                    "pip install pymupdf        # 가장 권장 (강력한 기능)\n"
                    "pip install pdfplumber     # 테이블 처리 우수\n"
                    "pip install pdfminer.six   # 레이아웃 분석\n"
                    "pip install pypdf          # 기본 텍스트 추출\n"
                )

        print(f"📋 사용 방법: {self.method}")
        print(f"   사용 가능: {', '.join(self.available_methods)}")

    def convert_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        PyMuPDF를 사용한 고급 변환 (가장 강력)

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            변환 결과
        """
        result = {
            "method": "pymupdf",
            "file": pdf_path,
            "pages": [],
            "total_pages": 0,
            "full_text": "",
            "metadata": {},
            "images": [],
            "links": [],
            "annotations": []
        }

        try:
            doc = fitz.open(pdf_path)
            result["total_pages"] = len(doc)

            # 메타데이터 추출
            result["metadata"] = doc.metadata

            all_text = []

            for page_num, page in enumerate(doc, 1):
                # 텍스트 추출 (다양한 방법)
                text = page.get_text("text")  # 기본 텍스트
                blocks = page.get_text("blocks")  # 블록 단위
                words = page.get_text("words")  # 단어 단위

                # 이미지 추출
                image_list = page.get_images()
                images_info = []
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n < 5:  # GRAY or RGB
                        images_info.append({
                            "page": page_num,
                            "index": img_index,
                            "width": pix.width,
                            "height": pix.height,
                            "size": len(pix.samples)
                        })
                    pix = None

                # 링크 추출
                links = []
                for link in page.get_links():
                    links.append({
                        "page": page_num,
                        "type": link.get("kind", ""),
                        "uri": link.get("uri", ""),
                        "rect": str(link.get("from", ""))
                    })

                # 주석 추출
                annotations = []
                for annot in page.annots():
                    annotations.append({
                        "page": page_num,
                        "type": annot.type[1],
                        "content": annot.info.get("content", ""),
                        "author": annot.info.get("title", "")
                    })

                page_result = {
                    "page": page_num,
                    "text": text,
                    "char_count": len(text),
                    "word_count": len(words),
                    "block_count": len(blocks),
                    "images": images_info,
                    "links": links,
                    "annotations": annotations
                }

                result["pages"].append(page_result)
                result["images"].extend(images_info)
                result["links"].extend(links)
                result["annotations"].extend(annotations)

                all_text.append(f"--- Page {page_num} ---\n{text}")

            result["full_text"] = "\n\n".join(all_text)
            result["status"] = "success"

            doc.close()

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def convert_with_pdfminer(self, pdf_path: str) -> Dict[str, Any]:
        """
        pdfminer를 사용한 레이아웃 기반 변환

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            변환 결과
        """
        result = {
            "method": "pdfminer",
            "file": pdf_path,
            "pages": [],
            "total_pages": 0,
            "full_text": "",
            "metadata": {},
            "layout_info": []
        }

        try:
            # 기본 텍스트 추출
            laparams = LAParams(
                line_overlap=0.5,
                char_margin=2.0,
                word_margin=0.1,
                boxes_flow=0.5,
                detect_vertical=True
            )

            full_text = extract_text(pdf_path, laparams=laparams)
            result["full_text"] = full_text

            # 페이지별 레이아웃 분석
            pages = list(extract_pages(pdf_path, laparams=laparams))
            result["total_pages"] = len(pages)

            for page_num, page_layout in enumerate(pages, 1):
                page_text = ""
                text_boxes = []

                for element in page_layout:
                    if isinstance(element, LTTextBox):
                        text = element.get_text()
                        page_text += text
                        text_boxes.append({
                            "x": element.x0,
                            "y": element.y0,
                            "width": element.width,
                            "height": element.height,
                            "text": text.strip()
                        })

                result["pages"].append({
                    "page": page_num,
                    "text": page_text,
                    "char_count": len(page_text),
                    "text_boxes": len(text_boxes),
                    "layout": text_boxes[:5]  # 처음 5개만 저장
                })

            result["status"] = "success"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def convert_with_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """
        pdfplumber를 사용한 변환 (테이블 처리 강화)

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            변환 결과
        """
        result = {
            "method": "pdfplumber",
            "file": pdf_path,
            "pages": [],
            "total_pages": 0,
            "full_text": "",
            "metadata": {},
            "tables": [],
            "forms": []
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                result["metadata"] = pdf.metadata if pdf.metadata else {}
                result["total_pages"] = len(pdf.pages)

                all_text = []

                for page_num, page in enumerate(pdf.pages, 1):
                    # 텍스트 추출
                    page_text = page.extract_text() or ""

                    # 테이블 추출 (개선된 설정)
                    table_settings = {
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                        "explicit_vertical_lines": [],
                        "explicit_horizontal_lines": [],
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                        "edge_min_length": 3,
                        "min_words_vertical": 1,
                        "min_words_horizontal": 1,
                        "text_tolerance": 3,
                    }

                    tables = page.extract_tables(table_settings=table_settings)
                    table_data = []

                    if tables:
                        for table_idx, table in enumerate(tables):
                            # 빈 셀 처리
                            cleaned_table = []
                            for row in table:
                                cleaned_row = [cell if cell else "" for cell in row]
                                cleaned_table.append(cleaned_row)

                            table_text = "\n".join(["\t".join(row) for row in cleaned_table])
                            table_data.append({
                                "table_index": table_idx + 1,
                                "rows": len(cleaned_table),
                                "cols": len(cleaned_table[0]) if cleaned_table else 0,
                                "data": cleaned_table,
                                "text": table_text
                            })

                    # 폼 필드 추출 (있는 경우)
                    if hasattr(page, 'annots') and page.annots:
                        for annot in page.annots:
                            if annot.get('subtype') == 'Widget':
                                result["forms"].append({
                                    "page": page_num,
                                    "field_type": annot.get('field_type', ''),
                                    "field_name": annot.get('field_name', ''),
                                    "field_value": annot.get('field_value', '')
                                })

                    # 단어 추출 (위치 정보 포함)
                    words = page.extract_words(
                        x_tolerance=3,
                        y_tolerance=3,
                        keep_blank_chars=False,
                        use_text_flow=True
                    )

                    page_result = {
                        "page": page_num,
                        "text": page_text,
                        "char_count": len(page_text),
                        "word_count": len(words),
                        "tables": table_data,
                        "has_images": len(page.images) > 0 if hasattr(page, 'images') else False
                    }

                    result["pages"].append(page_result)

                    # 전체 텍스트 구성
                    page_full_text = f"--- Page {page_num} ---\n{page_text}"
                    if table_data:
                        page_full_text += f"\n\n[Tables: {len(table_data)}]"
                        for table in table_data:
                            page_full_text += f"\n\nTable {table['table_index']} ({table['rows']}x{table['cols']}):\n{table['text']}"

                    all_text.append(page_full_text)

                    # 테이블 정보 저장
                    if table_data:
                        result["tables"].extend([{
                            "page": page_num,
                            **table
                        } for table in table_data])

                result["full_text"] = "\n\n".join(all_text)
                result["status"] = "success"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def convert_with_pypdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        pypdf (최신 PyPDF2)를 사용한 변환

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            변환 결과
        """
        result = {
            "method": "pypdf",
            "file": pdf_path,
            "pages": [],
            "total_pages": 0,
            "full_text": "",
            "metadata": {},
            "outline": []
        }

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)

                # 메타데이터 추출
                if pdf_reader.metadata:
                    result["metadata"] = {
                        "title": pdf_reader.metadata.get('/Title', ''),
                        "author": pdf_reader.metadata.get('/Author', ''),
                        "subject": pdf_reader.metadata.get('/Subject', ''),
                        "creator": pdf_reader.metadata.get('/Creator', ''),
                        "producer": pdf_reader.metadata.get('/Producer', ''),
                        "creation_date": str(pdf_reader.metadata.get('/CreationDate', '')),
                        "modification_date": str(pdf_reader.metadata.get('/ModDate', ''))
                    }

                # 아웃라인 (북마크) 추출
                try:
                    if hasattr(pdf_reader, 'outline'):
                        outline = pdf_reader.outline
                        if outline:
                            result["outline"] = self._parse_outline(outline)
                except:
                    pass

                # 페이지별 텍스트 추출
                result["total_pages"] = len(pdf_reader.pages)
                all_text = []

                for page_num, page in enumerate(pdf_reader.pages, 1):
                    # 다양한 추출 옵션 시도
                    try:
                        # 기본 텍스트 추출
                        page_text = page.extract_text()

                        # 레이아웃 보존 옵션 (최신 pypdf)
                        if hasattr(page, 'extract_text'):
                            layout_text = page.extract_text(
                                extraction_mode="layout",
                                layout_mode_space_vertically=False
                            ) if "extraction_mode" in page.extract_text.__code__.co_varnames else page_text
                        else:
                            layout_text = page_text

                    except:
                        page_text = page.extract_text() if hasattr(page, 'extract_text') else str(page)
                        layout_text = page_text

                    result["pages"].append({
                        "page": page_num,
                        "text": page_text,
                        "layout_text": layout_text,
                        "char_count": len(page_text)
                    })

                    all_text.append(f"--- Page {page_num} ---\n{page_text}")

                result["full_text"] = "\n\n".join(all_text)
                result["status"] = "success"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def _parse_outline(self, outline, level=0):
        """아웃라인 파싱"""
        parsed = []
        for item in outline:
            if isinstance(item, list):
                parsed.extend(self._parse_outline(item, level + 1))
            else:
                parsed.append({
                    "title": item.title if hasattr(item, 'title') else str(item),
                    "level": level,
                    "page": item.page if hasattr(item, 'page') else None
                })
        return parsed

    def convert_with_ocr(self, pdf_path: str, language: str = 'eng+kor') -> Dict[str, Any]:
        """
        OCR을 사용한 스캔 PDF 변환

        Args:
            pdf_path: PDF 파일 경로
            language: OCR 언어 (eng, kor, eng+kor 등)

        Returns:
            변환 결과
        """
        if not OCR_AVAILABLE:
            return {
                "status": "error",
                "error": "OCR 라이브러리가 설치되지 않았습니다. pip install pdf2image pytesseract pillow"
            }

        result = {
            "method": "ocr",
            "file": pdf_path,
            "pages": [],
            "total_pages": 0,
            "full_text": "",
            "language": language,
            "metadata": {}
        }

        try:
            # PDF를 이미지로 변환
            print("🔍 OCR 처리 중... (시간이 걸릴 수 있습니다)")
            images = convert_from_path(pdf_path, dpi=300)
            result["total_pages"] = len(images)

            all_text = []

            for page_num, image in enumerate(images, 1):
                print(f"   OCR 처리: 페이지 {page_num}/{len(images)}")

                # OCR 실행
                page_text = pytesseract.image_to_string(image, lang=language)

                # OCR 신뢰도 데이터
                ocr_data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
                confidence_scores = [c for c in ocr_data['conf'] if c > 0]
                avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

                result["pages"].append({
                    "page": page_num,
                    "text": page_text,
                    "char_count": len(page_text),
                    "confidence": avg_confidence,
                    "image_size": f"{image.width}x{image.height}"
                })

                all_text.append(f"--- Page {page_num} (OCR) ---\n{page_text}")

            result["full_text"] = "\n\n".join(all_text)
            result["status"] = "success"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def convert(self, pdf_path: str, fallback: bool = True) -> Dict[str, Any]:
        """
        PDF를 텍스트로 변환 (자동 방법 선택)

        Args:
            pdf_path: PDF 파일 경로
            fallback: 실패 시 다른 방법 시도

        Returns:
            변환 결과
        """
        if not os.path.exists(pdf_path):
            return {
                "status": "error",
                "error": f"File not found: {pdf_path}"
            }

        file_size = os.path.getsize(pdf_path)
        print(f"\n📄 Processing: {pdf_path}")
        print(f"   Size: {file_size:,} bytes")

        # 선택된 방법으로 시도
        result = None
        methods_to_try = [self.method]

        if fallback:
            # 폴백 순서 추가
            for method in ["pymupdf", "pdfplumber", "pdfminer", "pypdf"]:
                if method != self.method and method in self.available_methods:
                    methods_to_try.append(method)

        for method in methods_to_try:
            try:
                print(f"   시도: {method}")

                if method == "pymupdf":
                    result = self.convert_with_pymupdf(pdf_path)
                elif method == "pdfplumber":
                    result = self.convert_with_pdfplumber(pdf_path)
                elif method == "pdfminer":
                    result = self.convert_with_pdfminer(pdf_path)
                elif method == "pypdf":
                    result = self.convert_with_pypdf(pdf_path)
                elif method == "ocr":
                    result = self.convert_with_ocr(pdf_path)

                if result and result.get("status") == "success":
                    break

            except Exception as e:
                print(f"   ⚠️ {method} 실패: {str(e)}")
                continue

        # 텍스트가 거의 없으면 OCR 시도
        if result and result.get("status") == "success":
            text_length = len(result.get("full_text", ""))
            if text_length < 100 and self.enable_ocr and "ocr" in self.available_methods:
                print("   텍스트가 적음. OCR 시도...")
                ocr_result = self.convert_with_ocr(pdf_path)
                if ocr_result.get("status") == "success":
                    result = ocr_result

        # 통계 추가
        if result and result.get("status") == "success":
            result["statistics"] = {
                "file_size": file_size,
                "total_characters": len(result.get("full_text", "")),
                "total_pages": result.get("total_pages", 0),
                "average_chars_per_page": len(result.get("full_text", "")) // result.get("total_pages", 1) if result.get("total_pages", 0) > 0 else 0,
                "extraction_method": result.get("method", "unknown")
            }

        return result or {"status": "error", "error": "All methods failed"}

    def smart_extract(self, pdf_path: str) -> Dict[str, Any]:
        """
        스마트 추출 - PDF 특성을 분석하여 최적의 방법 자동 선택

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            변환 결과
        """
        print(f"\n🤖 Smart Extract: 최적 방법 자동 선택 중...")

        # 1. 먼저 빠른 분석
        analysis = self._analyze_pdf(pdf_path)

        # 2. 분석 결과에 따라 방법 선택
        if analysis.get("is_scanned"):
            print("   → 스캔 PDF 감지: OCR 사용")
            return self.convert_with_ocr(pdf_path)

        elif analysis.get("has_tables"):
            print("   → 테이블 감지: pdfplumber 사용")
            if "pdfplumber" in self.available_methods:
                return self.convert_with_pdfplumber(pdf_path)

        elif analysis.get("has_complex_layout"):
            print("   → 복잡한 레이아웃 감지: PyMuPDF 사용")
            if "pymupdf" in self.available_methods:
                return self.convert_with_pymupdf(pdf_path)

        else:
            print("   → 일반 PDF: 기본 방법 사용")
            return self.convert(pdf_path)

    def _analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """PDF 특성 빠른 분석"""
        analysis = {
            "is_scanned": False,
            "has_tables": False,
            "has_complex_layout": False,
            "has_forms": False,
            "page_count": 0
        }

        try:
            # 간단한 텍스트 추출 시도
            if PYPDF_AVAILABLE:
                with open(pdf_path, 'rb') as f:
                    reader = PdfReader(f)
                    analysis["page_count"] = len(reader.pages)

                    # 첫 페이지 텍스트 확인
                    if reader.pages:
                        first_page_text = reader.pages[0].extract_text()
                        # 텍스트가 거의 없으면 스캔 PDF일 가능성
                        if len(first_page_text.strip()) < 50:
                            analysis["is_scanned"] = True

                        # 테이블 패턴 감지 (간단한 휴리스틱)
                        if '\t' in first_page_text or '|' in first_page_text:
                            analysis["has_tables"] = True

        except:
            pass

        return analysis

    def save_as_text(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        """텍스트 파일로 저장"""
        result = self.convert(pdf_path)

        if result["status"] != "success":
            raise Exception(f"Conversion failed: {result.get('error', 'Unknown error')}")

        if output_path is None:
            pdf_name = Path(pdf_path).stem
            output_path = f"{pdf_name}_converted.txt"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"PDF to Text Conversion (Advanced)\n")
            f.write(f"{'=' * 80}\n")
            f.write(f"Source: {pdf_path}\n")
            f.write(f"Converted: {datetime.now().isoformat()}\n")
            f.write(f"Method: {result.get('method', 'unknown')}\n")
            f.write(f"Total Pages: {result.get('total_pages', 0)}\n")
            f.write(f"Total Characters: {len(result.get('full_text', '')):,}\n")

            if result.get('metadata'):
                f.write(f"\nMetadata:\n")
                for key, value in result['metadata'].items():
                    if value:
                        f.write(f"  {key}: {value}\n")

            f.write(f"\n{'=' * 80}\n\n")
            f.write(result.get('full_text', ''))

        print(f"💾 Saved to: {output_path}")
        return output_path

    def save_as_json(self, pdf_path: str, output_path: Optional[str] = None, compact: bool = False) -> str:
        """JSON으로 저장"""
        result = self.convert(pdf_path)

        if result["status"] != "success":
            raise Exception(f"Conversion failed: {result.get('error', 'Unknown error')}")

        if output_path is None:
            pdf_name = Path(pdf_path).stem
            output_path = f"{pdf_name}_converted.json"

        # Compact 모드: 큰 데이터 제거
        if compact:
            compact_result = {
                "status": result["status"],
                "method": result.get("method"),
                "file": result.get("file"),
                "total_pages": result.get("total_pages"),
                "full_text": result.get("full_text"),
                "metadata": result.get("metadata"),
                "statistics": result.get("statistics")
            }
            result = compact_result

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"💾 Saved to: {output_path}")
        return output_path


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Advanced PDF to Text Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf                    # 기본 변환
  %(prog)s document.pdf -m pymupdf        # PyMuPDF 사용
  %(prog)s document.pdf --ocr             # OCR 활성화
  %(prog)s document.pdf --smart           # 스마트 추출
  %(prog)s *.pdf -d output/               # 일괄 변환
  %(prog)s scan.pdf --ocr -l kor+eng      # 한국어+영어 OCR
        """
    )

    parser.add_argument("pdf_files", nargs="+", help="PDF file(s) to convert")
    parser.add_argument("-m", "--method",
                       choices=["auto", "pypdf", "pdfplumber", "pymupdf", "pdfminer", "ocr"],
                       default="auto",
                       help="Extraction method (default: auto)")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--format",
                       choices=["text", "json", "json-compact"],
                       default="text",
                       help="Output format (default: text)")
    parser.add_argument("-d", "--directory", help="Output directory for batch conversion")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR for scanned PDFs")
    parser.add_argument("-l", "--language", default="eng+kor", help="OCR language (default: eng+kor)")
    parser.add_argument("--smart", action="store_true", help="Use smart extraction (auto-select best method)")
    parser.add_argument("--list-methods", action="store_true", help="List available methods")

    args = parser.parse_args()

    # 사용 가능한 방법 출력
    if args.list_methods:
        print("\n📋 Available Methods:")
        converter = AdvancedPDFConverter()
        for method in converter.available_methods:
            print(f"  ✅ {method}")
        print("\n💡 Install more methods:")
        print("  pip install pymupdf        # Most powerful")
        print("  pip install pdfplumber     # Table extraction")
        print("  pip install pdfminer.six   # Layout analysis")
        print("  pip install pdf2image pytesseract  # OCR support")
        return

    # Converter 초기화
    converter = AdvancedPDFConverter(method=args.method, enable_ocr=args.ocr)

    # 단일 파일 처리
    if len(args.pdf_files) == 1:
        pdf_path = args.pdf_files[0]

        try:
            # 스마트 추출 또는 일반 변환
            if args.smart:
                result = converter.smart_extract(pdf_path)
            else:
                result = converter.convert(pdf_path)

            # 저장
            if args.format == "json":
                output_path = converter.save_as_json(pdf_path, args.output)
            elif args.format == "json-compact":
                output_path = converter.save_as_json(pdf_path, args.output, compact=True)
            else:
                output_path = converter.save_as_text(pdf_path, args.output)

            print(f"\n✅ Conversion completed: {output_path}")

            # 통계 출력
            if result.get("statistics"):
                stats = result["statistics"]
                print(f"\n📊 Statistics:")
                print(f"   Pages: {stats.get('total_pages', 0)}")
                print(f"   Characters: {stats.get('total_characters', 0):,}")
                print(f"   Method: {stats.get('extraction_method', 'unknown')}")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return 1

    # 여러 파일 일괄 처리
    else:
        output_dir = args.directory or "."
        os.makedirs(output_dir, exist_ok=True)

        success_count = 0
        for pdf_path in args.pdf_files:
            try:
                print(f"\n[Processing] {pdf_path}")
                pdf_name = Path(pdf_path).stem

                if args.smart:
                    result = converter.smart_extract(pdf_path)
                else:
                    result = converter.convert(pdf_path)

                if args.format == "json":
                    output_path = os.path.join(output_dir, f"{pdf_name}.json")
                    converter.save_as_json(pdf_path, output_path)
                elif args.format == "json-compact":
                    output_path = os.path.join(output_dir, f"{pdf_name}.json")
                    converter.save_as_json(pdf_path, output_path, compact=True)
                else:
                    output_path = os.path.join(output_dir, f"{pdf_name}.txt")
                    converter.save_as_text(pdf_path, output_path)

                success_count += 1

            except Exception as e:
                print(f"❌ Failed: {str(e)}")

        print(f"\n✅ Batch conversion completed: {success_count}/{len(args.pdf_files)} files")


if __name__ == "__main__":
    main()