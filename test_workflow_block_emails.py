#!/usr/bin/env python3
"""
Workflow implementation:
1. Query last week's emails for kimghw
2. Filter emails from block@krs.co.kr
3. Get detailed info for those specific emails
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_outlook.mail_service import MailService
from mcp_outlook.outlook_types import FilterParams, SelectParams
from mcp_outlook.graph_mail_client import QueryMethod

async def find_block_emails_workflow():
    """
    Workflow to find emails from block@krs.co.kr in the last week
    """
    print("=" * 80)
    print("📧 Workflow: 최근 일주일 kimghw 수신 메일 중 block@krs.co.kr 발신 메일 조회")
    print("=" * 80)

    # Initialize mail service
    mail_service = MailService()
    await mail_service.initialize()
    print("✅ Mail service initialized\n")

    user_email = "kimghw@krs.co.kr"
    target_sender = "block@krs.co.kr"

    # Step 1: Query last week's emails
    print("📋 Step 1: 최근 일주일 메일 조회")
    print("-" * 60)

    # Set date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    filter_params = FilterParams(
        received_date_from=start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        received_date_to=end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    print(f"📅 조회 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"👤 수신자: {user_email}")

    # Query with minimal fields first (id, subject, sender)
    select_params = SelectParams(
        id=True,
        subject=True,
        sender=True,
        received_date_time=True
    )

    print(f"\n🔄 메일 목록 조회 중...")

    result = await mail_service.query_mail_list(
        user_email=user_email,
        query_method=QueryMethod.FILTER,
        filter_params=filter_params,
        select_params=select_params,
        top=100  # Get more emails to find block emails
    )

    if not result.get("success"):
        print(f"❌ 메일 조회 실패: {result.get('error')}")
        return

    all_emails = result.get("emails", [])
    print(f"✅ 전체 {len(all_emails)}개 메일 조회 완료")

    # Step 2: Filter emails from block@krs.co.kr
    print("\n" + "=" * 80)
    print(f"📋 Step 2: {target_sender} 발신 메일 필터링")
    print("-" * 60)

    block_emails = []
    block_email_ids = []

    for email in all_emails:
        sender_info = email.get('sender', {})
        if sender_info:
            sender_address = sender_info.get('emailAddress', {}).get('address', '')
            if sender_address.lower() == target_sender.lower():
                block_emails.append(email)
                block_email_ids.append(email['id'])

    print(f"\n🔍 필터링 결과:")
    print(f"  - 전체 메일: {len(all_emails)}개")
    print(f"  - {target_sender} 발신 메일: {len(block_emails)}개")

    if not block_emails:
        print(f"\n❌ {target_sender}에서 발신한 메일이 없습니다.")
        return

    # Show summary of filtered emails
    print(f"\n📧 {target_sender} 발신 메일 목록:")
    print("-" * 60)
    for i, email in enumerate(block_emails, 1):
        print(f"{i}. {email.get('subject', 'N/A')}")
        print(f"   Date: {email.get('receivedDateTime', 'N/A')}")
        print(f"   ID: {email.get('id', 'N/A')[:50]}...")

    # Step 3: Get detailed info using mail_query_with_ID
    print("\n" + "=" * 80)
    print("📋 Step 3: mail_query_with_ID로 상세 정보 조회")
    print("-" * 60)

    # Use batch_and_fetch to get detailed information
    print(f"\n🔄 {len(block_email_ids)}개 메일 상세 정보 조회 중...")

    # Get full details with more fields
    detailed_select_params = SelectParams(
        id=True,
        subject=True,
        body_preview=True,
        sender=True,
        from_recipient=True,
        received_date_time=True,
        has_attachments=True,
        importance=True,
        internet_message_id=True
    )

    batch_result = await mail_service.batch_and_fetch(
        user_email=user_email,
        message_ids=block_email_ids,
        select_params=detailed_select_params
    )

    if batch_result.get("success") or "value" in batch_result:
        detailed_emails = batch_result.get("value", batch_result.get("emails", []))
        print(f"\n✅ {len(detailed_emails)}개 메일 상세 정보 조회 완료")

        # Display detailed information
        print("\n" + "=" * 80)
        print("📊 상세 메일 정보")
        print("=" * 80)

        for i, email in enumerate(detailed_emails, 1):
            print(f"\n--- 메일 {i} ---")
            print(f"제목: {email.get('subject', 'N/A')}")

            sender_info = email.get('sender', {})
            if sender_info:
                sender_name = sender_info.get('emailAddress', {}).get('name', 'N/A')
                sender_address = sender_info.get('emailAddress', {}).get('address', 'N/A')
                print(f"발신자: {sender_name} <{sender_address}>")

            print(f"수신 시간: {email.get('receivedDateTime', 'N/A')}")
            print(f"첨부파일: {'있음' if email.get('hasAttachments') else '없음'}")
            print(f"중요도: {email.get('importance', 'N/A')}")

            # Show preview
            preview = email.get('bodyPreview', '')
            if preview:
                print(f"미리보기:")
                print(f"  {preview[:200]}...")

            print(f"Message ID: {email.get('internetMessageId', 'N/A')}")

        # Statistics
        print("\n" + "=" * 80)
        print("📊 통계")
        print("-" * 60)

        with_attachments = sum(1 for e in detailed_emails if e.get('hasAttachments'))
        print(f"총 {target_sender} 발신 메일: {len(detailed_emails)}개")
        print(f"첨부파일 포함 메일: {with_attachments}개")

        # Date range analysis
        dates = []
        for email in detailed_emails:
            date_str = email.get('receivedDateTime')
            if date_str:
                try:
                    dates.append(datetime.fromisoformat(date_str.replace('Z', '+00:00')))
                except:
                    pass

        if dates:
            oldest = min(dates)
            newest = max(dates)
            print(f"메일 수신 기간: {oldest.strftime('%Y-%m-%d %H:%M')} ~ {newest.strftime('%Y-%m-%d %H:%M')}")

    else:
        print(f"❌ 상세 정보 조회 실패: {batch_result.get('error')}")

    # Cleanup
    if hasattr(mail_service, '_client') and mail_service._client:
        await mail_service._client.close()

    print("\n" + "=" * 80)
    print("✅ Workflow 완료")
    print("=" * 80)

async def main():
    await find_block_emails_workflow()

if __name__ == "__main__":
    asyncio.run(main())