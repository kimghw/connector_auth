#!/usr/bin/env python3
"""
인증 대기 목록 조회
block@krs.co.kr에서 온 메일 중 "[인증 요청]" 태그가 있는 메일들을 조회
"""

import asyncio
import json
import sys
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_outlook.mail_service import MailService
from mcp_outlook.outlook_types import FilterParams, SelectParams
from mcp_outlook.graph_mail_client import QueryMethod

async def find_auth_pending_emails():
    """
    인증 대기 중인 메일 목록 조회
    """
    print("=" * 80)
    print("📧 인증 대기 목록 조회")
    print("=" * 80)

    # Initialize mail service
    mail_service = MailService()
    await mail_service.initialize()
    print("✅ Mail service initialized\n")

    user_email = "kimghw@krs.co.kr"
    target_sender = "block@krs.co.kr"

    # Get recent emails (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    filter_params = FilterParams(
        received_date_from=start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        received_date_to=end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    print(f"📅 조회 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"🔍 대상: {target_sender} 발신 메일 중 인증 대기 목록\n")

    # Step 1: Get emails from block@krs.co.kr
    print("Step 1: block@krs.co.kr 메일 조회")
    print("-" * 60)

    select_params = SelectParams(
        id=True,
        subject=True,
        sender=True,
        received_date_time=True,
        body_preview=True
    )

    result = await mail_service.query_mail_list(
        user_email=user_email,
        query_method=QueryMethod.FILTER,
        filter_params=filter_params,
        select_params=select_params,
        top=100
    )

    if not result.get("success"):
        print(f"❌ 메일 조회 실패: {result.get('error')}")
        return

    # Filter for block emails
    all_emails = result.get("emails", [])
    block_emails = []
    auth_pending_emails = []

    for email in all_emails:
        sender_info = email.get('sender', {})
        if sender_info:
            sender_address = sender_info.get('emailAddress', {}).get('address', '')
            if sender_address.lower() == target_sender.lower():
                block_emails.append(email)

                # Check if it's an auth pending email
                subject = email.get('subject', '')
                if '[인증 요청]' in subject or 'Certification request' in subject:
                    auth_pending_emails.append(email)

    print(f"✅ 전체 {len(all_emails)}개 메일 중 {len(block_emails)}개가 {target_sender}에서 발신")
    print(f"✅ 그 중 {len(auth_pending_emails)}개가 인증 대기 메일\n")

    if not auth_pending_emails:
        print("❌ 인증 대기 중인 메일이 없습니다.")
        return

    # Step 2: Get detailed information for auth pending emails
    print("Step 2: 인증 대기 메일 상세 정보 조회")
    print("-" * 60)

    auth_ids = [email['id'] for email in auth_pending_emails]

    # Get full body to extract auth expiration info
    select_params_full = SelectParams(
        id=True,
        subject=True,
        body=True,
        body_preview=True,
        sender=True,
        from_recipient=True,
        received_date_time=True,
        internet_message_id=True
    )

    print(f"🔄 {len(auth_ids)}개 인증 대기 메일 상세 조회 중...\n")

    batch_result = await mail_service.batch_and_fetch(
        user_email=user_email,
        message_ids=auth_ids,
        select_params=select_params_full
    )

    if batch_result.get("success") or "value" in batch_result:
        detailed_emails = batch_result.get("value", batch_result.get("emails", []))

        print(f"✅ {len(detailed_emails)}개 인증 대기 메일 상세 조회 완료\n")
        print("=" * 80)
        print("📋 인증 대기 목록")
        print("=" * 80)

        auth_list = []

        for i, email in enumerate(detailed_emails, 1):
            subject = email.get('subject', '')
            received_date = email.get('receivedDateTime', '')
            body_preview = email.get('bodyPreview', '')

            # Extract the actual subject (remove auth tags)
            actual_subject = subject.replace('[인증 요청]', '').replace('[Certification request]', '')
            actual_subject = actual_subject.replace('본 메일은 인증 요청 메일 입니다.', '')
            actual_subject = actual_subject.replace('This is an authentication request mail.', '')
            actual_subject = actual_subject.strip()

            # Try to extract expiration date from body
            expiration_date = None
            if '인증 만료 시간' in body_preview:
                match = re.search(r'인증 만료 시간\s*[:：]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', body_preview)
                if match:
                    expiration_date = match.group(1)

            # Try to extract original sender from subject
            original_sender = "Unknown"
            if '👤' in actual_subject:
                # Facebook friend recommendation
                original_sender = "Facebook"
            elif '[' in actual_subject and ']' in actual_subject:
                # Extract company/service name from brackets
                match = re.search(r'\[([^\]]+)\]', actual_subject)
                if match:
                    original_sender = match.group(1)

            auth_info = {
                'no': i,
                'subject': actual_subject,
                'original_sender': original_sender,
                'received_date': received_date,
                'expiration_date': expiration_date,
                'id': email.get('id')
            }
            auth_list.append(auth_info)

            print(f"\n--- {i}. 인증 대기 메일 ---")
            print(f"제목: {actual_subject}")
            print(f"원 발신자: {original_sender}")
            print(f"수신 시간: {received_date}")

            if expiration_date:
                print(f"인증 만료: {expiration_date}")

                # Check if expired
                try:
                    exp_dt = datetime.strptime(expiration_date, "%Y-%m-%d %H:%M")
                    if exp_dt < datetime.now():
                        print("⚠️  상태: 만료됨")
                    else:
                        remaining = exp_dt - datetime.now()
                        print(f"✅ 상태: 유효 (남은 시간: {remaining.days}일 {remaining.seconds//3600}시간)")
                except:
                    pass

        # Summary table
        print("\n" + "=" * 80)
        print("📊 인증 대기 목록 요약")
        print("=" * 80)
        print(f"\n총 {len(auth_list)}개의 인증 대기 메일\n")

        print("번호 | 원 발신자 | 제목 | 수신일 | 만료일")
        print("-" * 80)

        for auth in auth_list:
            received = auth['received_date'][:10] if auth['received_date'] else 'N/A'
            expiration = auth['expiration_date'] if auth['expiration_date'] else '정보 없음'
            subject_short = auth['subject'][:30] + '...' if len(auth['subject']) > 30 else auth['subject']

            print(f"{auth['no']:3d} | {auth['original_sender']:15s} | {subject_short:35s} | {received} | {expiration}")

        # Group by original sender
        print("\n" + "=" * 80)
        print("📊 발신자별 통계")
        print("-" * 60)

        sender_stats = {}
        for auth in auth_list:
            sender = auth['original_sender']
            if sender not in sender_stats:
                sender_stats[sender] = 0
            sender_stats[sender] += 1

        for sender, count in sorted(sender_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {sender}: {count}개")

    else:
        print(f"❌ 상세 조회 실패: {batch_result.get('error')}")

    # Cleanup
    if hasattr(mail_service, '_client') and mail_service._client:
        await mail_service._client.close()

    print("\n" + "=" * 80)
    print("✅ 인증 대기 목록 조회 완료")
    print("=" * 80)

async def main():
    await find_auth_pending_emails()

if __name__ == "__main__":
    asyncio.run(main())