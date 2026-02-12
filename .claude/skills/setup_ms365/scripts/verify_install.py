"""
MS365 MCP 서버 설치 검증 스크립트

venv에서 실행하여 핵심 패키지 import와 서버 엔트리포인트를 검증합니다.

사용법 (venv python으로 실행):
    /mnt/c/connector_auth/venv/Scripts/python.exe verify_install.py {server_name}
    /mnt/c/connector_auth/venv/Scripts/python.exe verify_install.py outlook
    /mnt/c/connector_auth/venv/Scripts/python.exe verify_install.py calendar
"""

import sys

CORE_MODULES = ["aiohttp", "pydantic", "yaml", "dotenv"]


def check_imports():
    """핵심 패키지 import 테스트"""
    failed = []
    for mod in CORE_MODULES:
        try:
            __import__(mod)
        except ImportError:
            failed.append(mod)
    return failed


def check_server_entry(server_name):
    """서버 엔트리포인트 파일 존재 확인"""
    from pathlib import Path
    # 프로젝트 루트 기준
    project_root = Path(__file__).resolve().parents[3]
    server_path = project_root / f"mcp_{server_name}" / "mcp_server" / "server_stdio.py"
    # fallback: 절대경로
    if not server_path.exists():
        server_path = Path(f"C:/connector_auth/mcp_{server_name}/mcp_server/server_stdio.py")
    return server_path.exists(), str(server_path)


def main():
    # 서버명 인자 처리
    if len(sys.argv) > 1:
        server_name = sys.argv[1]
    else:
        server_name = "outlook"
        print(f"[INFO] 서버명 미지정, 기본값 사용: {server_name}")

    print(f"Python: {sys.version}")
    print(f"경로:   {sys.executable}")
    print(f"서버:   {server_name}")
    print()

    # Import 검증
    failed = check_imports()
    if failed:
        print(f"[FAIL] import 실패: {', '.join(failed)}")
        sys.exit(1)
    else:
        print(f"[OK] 핵심 패키지 import 성공: {', '.join(CORE_MODULES)}")

    # 서버 엔트리포인트 검증
    exists, path = check_server_entry(server_name)
    if exists:
        print(f"[OK] 서버 엔트리포인트 존재: {path}")
    else:
        print(f"[WARN] 서버 엔트리포인트 없음: {path}")

    print()
    print("검증 완료")


if __name__ == "__main__":
    main()
