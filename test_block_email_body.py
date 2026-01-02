#!/usr/bin/env python3
"""
Test fetching full body content of block@krs.co.kr emails
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_outlook.mail_service import MailService
from mcp_outlook.outlook_types import FilterParams, SelectParams
from mcp_outlook.graph_mail_client import QueryMethod

async def test_block_email_body():
    """
    Test fetching body content from block@krs.co.kr emails
    """
    print("=" * 80)
    print("📧 Testing block@krs.co.kr 메일 본문 내용 조회")
    print("=" * 80)

    # Initialize mail service
    mail_service = MailService()
    await mail_service.initialize()
    print("✅ Mail service initialized\n")

    user_email = "kimghw@krs.co.kr"
    target_sender = "block@krs.co.kr"

    # Get recent emails (last 3 days for quicker test)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)

    filter_params = FilterParams(
        received_date_from=start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        received_date_to=end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    print(f"📅 조회 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"🔍 대상 발신자: {target_sender}\n")

    # First, get email IDs from block@krs.co.kr
    print("Step 1: 메일 목록 조회")
    print("-" * 60)

    select_params_minimal = SelectParams(
        id=True,
        subject=True,
        sender=True
    )

    result = await mail_service.query_mail_list(
        user_email=user_email,
        query_method=QueryMethod.FILTER,
        filter_params=filter_params,
        select_params=select_params_minimal,
        top=50
    )

    if not result.get("success"):
        print(f"❌ 메일 조회 실패: {result.get('error')}")
        return

    # Filter for block emails
    all_emails = result.get("emails", [])
    block_emails = []

    for email in all_emails:
        sender_info = email.get('sender', {})
        if sender_info:
            sender_address = sender_info.get('emailAddress', {}).get('address', '')
            if sender_address.lower() == target_sender.lower():
                block_emails.append(email)

    print(f"✅ {target_sender}에서 {len(block_emails)}개 메일 발견\n")

    if not block_emails:
        print("❌ block@krs.co.kr 메일이 없습니다.")
        return

    # Get first 3 block emails for testing
    test_emails = block_emails[:3]
    test_ids = [email['id'] for email in test_emails]

    print("Step 2: 본문 내용 포함 상세 조회")
    print("-" * 60)

    # Request full body content
    select_params_full = SelectParams(
        id=True,
        subject=True,
        body=True,  # Full HTML body
        body_preview=True,  # Text preview
        unique_body=True,  # Unique content without reply chain
        sender=True,
        received_date_time=True,
        internet_message_id=True
    )

    print(f"🔄 {len(test_ids)}개 메일 본문 조회 중...\n")

    batch_result = await mail_service.batch_and_fetch(
        user_email=user_email,
        message_ids=test_ids,
        select_params=select_params_full
    )

    if batch_result.get("success") or "value" in batch_result:
        detailed_emails = batch_result.get("value", batch_result.get("emails", []))

        print(f"✅ {len(detailed_emails)}개 메일 본문 조회 완료\n")
        print("=" * 80)

        for i, email in enumerate(detailed_emails, 1):
            print(f"\n📧 메일 {i}")
            print("=" * 80)
            print(f"제목: {email.get('subject', 'N/A')}")
            print(f"수신 시간: {email.get('receivedDateTime', 'N/A')}")
            print(f"Message ID: {email.get('internetMessageId', 'N/A')}")

            # Body Preview (plain text)
            print("\n📄 본문 미리보기 (Plain Text):")
            print("-" * 60)
            body_preview = email.get('bodyPreview', '')
            if body_preview:
                print(body_preview[:500])
                if len(body_preview) > 500:
                    print("... (truncated)")
            else:
                print("(미리보기 없음)")

            # Full Body Content
            print("\n📝 본문 전체 내용 확인:")
            print("-" * 60)

            body = email.get('body', {})
            if body:
                content_type = body.get('contentType', 'unknown')
                content = body.get('content', '')

                print(f"Content Type: {content_type}")
                print(f"Content Length: {len(content)} characters")

                if content:
                    if content_type == 'text':
                        # Plain text body
                        print("\n[Plain Text Body]:")
                        print(content[:1000])
                        if len(content) > 1000:
                            print("... (truncated)")
                    elif content_type == 'html':
                        # HTML body
                        print("\n[HTML Body] (first 1000 chars):")
                        print(content[:1000])
                        if len(content) > 1000:
                            print("... (truncated)")

                        # Try to extract text from HTML
                        import re
                        text_only = re.sub('<[^<]+?>', '', content)
                        text_only = text_only.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
                        text_only = ' '.join(text_only.split())

                        print("\n[Extracted Text from HTML]:")
                        print(text_only[:500])
                        if len(text_only) > 500:
                            print("... (truncated)")
                else:
                    print("(본문 내용 없음)")
            else:
                print("(body 필드 없음)")

            # Unique Body (without reply chain)
            unique_body = email.get('uniqueBody', {})
            if unique_body and unique_body.get('content'):
                print("\n📌 Unique Body (회신 체인 제외):")
                print("-" * 60)
                unique_content = unique_body.get('content', '')[:500]
                print(unique_content)
                if len(unique_body.get('content', '')) > 500:
                    print("... (truncated)")

            print("\n" + "=" * 80)

        # Summary
        print("\n📊 요약:")
        print("-" * 60)
        print(f"✅ {len(detailed_emails)}개 메일 본문 성공적으로 조회됨")

        body_found = sum(1 for e in detailed_emails if e.get('body', {}).get('content'))
        print(f"✅ {body_found}/{len(detailed_emails)}개 메일에서 본문 내용 확인")

    else:
        print(f"❌ 본문 조회 실패: {batch_result.get('error')}")

    # Cleanup
    if hasattr(mail_service, '_client') and mail_service._client:
        await mail_service._client.close()

    print("\n✅ Test completed")

async def main():
    await test_block_email_body()

if __name__ == "__main__":
    asyncio.run(main())