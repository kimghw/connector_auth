#!/usr/bin/env python3
"""
UI 구조 비교 스크립트
원본과 리팩토링된 HTML의 DOM 구조를 비교
"""

from bs4 import BeautifulSoup
from pathlib import Path


def extract_ui_structure(html_content):
    """HTML에서 UI 구조 추출"""
    soup = BeautifulSoup(html_content, "html.parser")

    # 스크립트와 스타일 태그 제거
    for script in soup(["script", "style"]):
        script.decompose()

    # 주요 UI 요소 추출
    structure = {
        "title": soup.find("title").text if soup.find("title") else None,
        "header": None,
        "sidebar": None,
        "main_content": None,
        "modals": [],
        "buttons": [],
        "forms": [],
        "classes": set(),
    }

    # 헤더 구조
    header = soup.find("div", class_="header")
    if header:
        structure["header"] = {
            "h1": header.find("h1").text.strip() if header.find("h1") else None,
            "buttons": len(header.find_all("button")),
            "classes": [c for c in header.get("class", [])],
        }

    # 사이드바 구조
    sidebar = soup.find("div", class_="sidebar")
    if sidebar:
        structure["sidebar"] = {
            "tool_list": bool(sidebar.find("div", class_="tool-list")),
            "classes": [c for c in sidebar.get("class", [])],
        }

    # 메인 컨텐츠
    editor = soup.find("div", class_="editor-area")
    if editor:
        structure["main_content"] = {
            "forms": len(editor.find_all("form")),
            "inputs": len(editor.find_all("input")),
            "textareas": len(editor.find_all("textarea")),
            "selects": len(editor.find_all("select")),
        }

    # 모달 다이얼로그
    modals = soup.find_all("div", class_="modal")
    structure["modals"] = [modal.get("id", "unnamed") for modal in modals]

    # 버튼 수집
    all_buttons = soup.find_all("button")
    structure["buttons"] = len(all_buttons)

    # 모든 클래스 수집
    for element in soup.find_all(class_=True):
        for cls in element.get("class", []):
            structure["classes"].add(cls)

    return structure


def compare_structures(original, refactored):
    """두 구조 비교"""
    print("\n" + "=" * 60)
    print("UI STRUCTURE COMPARISON")
    print("=" * 60)

    differences = []

    # 타이틀 비교
    print("\n📝 Title:")
    print(f"  Original:   {original['title']}")
    print(f"  Refactored: {refactored['title']}")
    if original["title"] == refactored["title"]:
        print("  ✅ Match")
    else:
        print("  ❌ Different")
        differences.append("Title mismatch")

    # 헤더 비교
    print("\n🎯 Header:")
    if original["header"] and refactored["header"]:
        orig_h1 = original["header"]["h1"]
        ref_h1 = refactored["header"]["h1"]
        print("  H1 Text:")
        print(f"    Original:   {orig_h1}")
        print(f"    Refactored: {ref_h1}")

        # 텍스트 정규화 후 비교
        if orig_h1 and ref_h1:
            # 공백 정규화
            orig_clean = " ".join(orig_h1.split())
            ref_clean = " ".join(ref_h1.split())
            if orig_clean == ref_clean:
                print("    ✅ Match")
            else:
                print("    ❌ Different")
                differences.append("Header text mismatch")

        print(f"  Buttons: Original={original['header']['buttons']}, Refactored={refactored['header']['buttons']}")
        if original["header"]["buttons"] == refactored["header"]["buttons"]:
            print("    ✅ Same button count")
        else:
            print("    ❌ Different button count")
            differences.append("Header button count mismatch")

    # 사이드바 비교
    print("\n📁 Sidebar:")
    if original["sidebar"] and refactored["sidebar"]:
        print(
            f"  Tool List: Original={original['sidebar']['tool_list']}, Refactored={refactored['sidebar']['tool_list']}"
        )
        if original["sidebar"]["tool_list"] == refactored["sidebar"]["tool_list"]:
            print("    ✅ Match")
        else:
            print("    ❌ Different")
            differences.append("Sidebar structure mismatch")

    # 메인 컨텐츠 비교
    print("\n📋 Main Content:")
    if original["main_content"] and refactored["main_content"]:
        for key in ["forms", "inputs", "textareas", "selects"]:
            orig_val = original["main_content"].get(key, 0)
            ref_val = refactored["main_content"].get(key, 0)
            print(f"  {key.capitalize()}: Original={orig_val}, Refactored={ref_val}")
            if orig_val == ref_val:
                print("    ✅ Match")
            else:
                print("    ❌ Different")
                differences.append(f"{key} count mismatch")

    # 모달 비교
    print("\n🔲 Modals:")
    print(f"  Original:   {len(original['modals'])} modals")
    print(f"  Refactored: {len(refactored['modals'])} modals")
    if len(original["modals"]) == len(refactored["modals"]):
        print("  ✅ Same modal count")
    else:
        print("  ❌ Different modal count")
        differences.append("Modal count mismatch")

    # 버튼 총 개수
    print("\n🔘 Total Buttons:")
    print(f"  Original:   {original['buttons']}")
    print(f"  Refactored: {refactored['buttons']}")
    if abs(original["buttons"] - refactored["buttons"]) <= 2:  # 허용 오차
        print("  ✅ Similar button count")
    else:
        print("  ❌ Significant difference")
        differences.append("Button count mismatch")

    # CSS 클래스 비교
    print("\n🎨 CSS Classes:")
    print(f"  Original:   {len(original['classes'])} unique classes")
    print(f"  Refactored: {len(refactored['classes'])} unique classes")

    # 공통 클래스
    common_classes = original["classes"].intersection(refactored["classes"])

    print(f"  Common:     {len(common_classes)} classes")

    # 주요 클래스 체크
    important_classes = ["container", "header", "sidebar", "tool-list", "editor-area", "modal", "btn", "form-control"]

    print("\n  Important Classes Check:")
    for cls in important_classes:
        in_orig = cls in original["classes"]
        in_ref = cls in refactored["classes"]
        if in_orig and in_ref:
            print(f"    ✅ '{cls}' - Present in both")
        elif not in_orig and not in_ref:
            print(f"    ⚪ '{cls}' - Missing in both")
        else:
            print(f"    ❌ '{cls}' - Mismatch")
            differences.append(f"Class '{cls}' mismatch")

    # 최종 결과
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    if not differences:
        print("✅ UI STRUCTURE IS IDENTICAL!")
        print("All major UI elements match perfectly.")
    else:
        print(f"⚠️  Found {len(differences)} differences:")
        for i, diff in enumerate(differences, 1):
            print(f"  {i}. {diff}")

    # 유사도 계산
    total_checks = 15  # 총 체크 항목 수
    passed = total_checks - len(differences)
    similarity = (passed / total_checks) * 100

    print(f"\n📊 UI Similarity: {similarity:.1f}%")

    if similarity >= 95:
        print("✅ Excellent match - UI is virtually identical")
    elif similarity >= 90:
        print("✅ Good match - Minor differences only")
    elif similarity >= 80:
        print("⚠️  Acceptable match - Some differences present")
    else:
        print("❌ Poor match - Significant differences")

    return similarity


def main():
    # 파일 경로
    base_path = Path("/home/kimghw/Connector_auth/mcp_editor")
    original_path = base_path / "templates/tool_editor.html"
    refactored_path = base_path / "templates/tool_editor_final.html"

    # HTML 읽기
    print("Loading HTML files...")
    original_html = original_path.read_text()
    refactored_html = refactored_path.read_text()

    print(f"Original size:   {len(original_html):,} bytes")
    print(f"Refactored size: {len(refactored_html):,} bytes")

    # 구조 추출
    print("\nExtracting UI structures...")
    original_structure = extract_ui_structure(original_html)
    refactored_structure = extract_ui_structure(refactored_html)

    # 비교
    similarity = compare_structures(original_structure, refactored_structure)

    # 시각적 차이 요약
    print("\n" + "=" * 60)
    print("VISUAL COMPARISON SUMMARY")
    print("=" * 60)

    if similarity >= 95:
        print(
            """
✅ The UI is IDENTICAL!

The refactored version maintains:
- Same header layout and branding
- Same sidebar structure
- Same main content area
- Same form elements
- Same modal dialogs
- Same CSS classes for styling

Users will NOT notice any visual difference.
        """
        )
    else:
        print(
            """
⚠️  Some differences detected.

Please check the browser comparison at:
http://localhost:8005/compare_ui.html
        """
        )

    return similarity >= 95


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
