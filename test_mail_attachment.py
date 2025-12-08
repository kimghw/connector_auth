#!/usr/bin/env python3
"""
메일 첨부 파일 조회 및 다운로드 테스트
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from outlook_mcp.graph_mail_attachment import GraphMailAttachmentHandler
from outlook_mcp.graph_mail_search import GraphMailSearcher

# .env 파일 로드
load_dotenv()


async def test_attachment_operations():
    """첨부 파일 작업 테스트"""

    # 액세스 토큰 가져오기
    access_token = os.getenv("GRAPH_ACCESS_TOKEN")
    if not access_token:
        print("❌ GRAPH_ACCESS_TOKEN not found in environment variables")
        print("Please run callback_server.py first to get the token")
        return

    print("🔑 Access token loaded successfully")
    print("="*60)

    # 메일 검색기와 첨부 파일 핸들러 초기화
    mail_searcher = GraphMailSearcher(access_token)
    attachment_handler = GraphMailAttachmentHandler(access_token)

    # 1. 최근 첨부 파일이 있는 메일 검색
    print("\n📧 Searching for recent emails with attachments...")

    # 최근 30일 내 첨부 파일이 있는 메일 검색
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    filter_params = {
        "hasAttachments": True,
        "receivedDateTime": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }

    try:
        # 메일 검색
        mails = await mail_searcher.search_messages(
            filter_params=filter_params,
            max_results=5,  # 최대 5개 메일만
            select_fields=["id", "subject", "from", "receivedDateTime", "hasAttachments"]
        )

        if not mails:
            print("No emails with attachments found in the last 30 days")
            return

        print(f"Found {len(mails)} email(s) with attachments:")
        for i, mail in enumerate(mails, 1):
            print(f"\n{i}. {mail.get('subject', 'No Subject')}")
            print(f"   From: {mail.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')}")
            print(f"   Date: {mail.get('receivedDateTime', 'Unknown')}")
            print(f"   ID: {mail.get('id')}")

        # 2. 첫 번째 메일의 첨부 파일 처리
        print("\n" + "="*60)
        print("📎 Processing attachments from the first email...")

        first_mail = mails[0]
        mail_id = first_mail.get("id")
        subject = first_mail.get("subject", "No Subject")

        print(f"\nSelected email: {subject}")

        # 첨부 파일 목록 조회
        attachments = await attachment_handler.list_attachments(mail_id)

        if not attachments:
            print("No attachments found (this shouldn't happen)")
            return

        print(f"\n📋 Attachment list ({len(attachments)} file(s)):")
        total_size = 0
        for att in attachments:
            size_mb = att['size'] / (1024 * 1024)
            print(f"   - {att['name']}")
            print(f"     Type: {att['contentType']}")
            print(f"     Size: {att['size']:,} bytes ({size_mb:.2f} MB)")
            print(f"     ID: {att['id']}")
            print(f"     Inline: {att['isInline']}")
            total_size += att['size']

        total_size_mb = total_size / (1024 * 1024)
        print(f"\n   Total size: {total_size:,} bytes ({total_size_mb:.2f} MB)")

        # 3. 첨부 파일 다운로드
        print("\n" + "="*60)
        print("💾 Downloading attachments...")

        # 다운로드 디렉토리 생성
        download_dir = Path("downloads") / datetime.now().strftime("%Y%m%d_%H%M%S")
        download_dir.mkdir(parents=True, exist_ok=True)

        print(f"Download directory: {download_dir}")

        # 모든 첨부 파일 다운로드
        downloaded_files = await attachment_handler.download_all_attachments(
            mail_id,
            save_dir=str(download_dir)
        )

        if downloaded_files:
            print(f"\n✅ Successfully downloaded {len(downloaded_files)} file(s):")
            for file_path in downloaded_files:
                file_size = Path(file_path).stat().st_size
                print(f"   - {Path(file_path).name} ({file_size:,} bytes)")

        # 4. 여러 메일의 첨부 파일 일괄 처리 (옵션)
        if len(mails) > 1:
            print("\n" + "="*60)
            print("📊 Batch processing attachments from multiple emails...")

            # 처음 3개 메일만 처리
            batch_mails = mails[:3]

            results = await attachment_handler.process_mail_attachments(
                batch_mails,
                download=True,
                save_dir="downloads/batch"
            )

            print("\n📈 Batch processing results:")
            print(json.dumps(results, indent=2, default=str))

        print("\n" + "="*60)
        print("✅ Attachment operations test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


async def test_specific_mail_attachment(mail_id: str):
    """특정 메일의 첨부 파일 테스트"""

    access_token = os.getenv("GRAPH_ACCESS_TOKEN")
    if not access_token:
        print("❌ GRAPH_ACCESS_TOKEN not found")
        return

    handler = GraphMailAttachmentHandler(access_token)

    try:
        print(f"📧 Processing mail ID: {mail_id}")

        # 첨부 파일 목록 조회
        attachments = await handler.list_attachments(mail_id)

        if not attachments:
            print("No attachments found")
            return

        print(f"Found {len(attachments)} attachment(s)")

        # 다운로드
        downloaded = await handler.download_all_attachments(mail_id)
        print(f"Downloaded {len(downloaded)} file(s)")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # 명령줄 인자로 특정 메일 ID를 받을 수 있음
    if len(sys.argv) > 1:
        mail_id = sys.argv[1]
        asyncio.run(test_specific_mail_attachment(mail_id))
    else:
        # 일반 테스트 실행
        asyncio.run(test_attachment_operations())