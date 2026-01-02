#!/usr/bin/env python3
"""
Test mail_query_with_ID tool
This tool fetches emails by their IDs using batch_and_fetch
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

async def test_mail_query_with_id():
    """Test mail_query_with_ID functionality"""
    print("=" * 60)
    print("Testing mail_query_with_ID tool")
    print("=" * 60)

    # Initialize mail service
    mail_service = MailService()
    await mail_service.initialize()
    print("✅ Mail service initialized\n")

    user_email = "kimghw@krs.co.kr"

    # Step 1: First get some mail IDs using mail_list
    print("📧 Step 1: Getting mail IDs using mail_list")
    print("-" * 40)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)

    filter_params = FilterParams(
        received_date_from=start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        received_date_to=end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    # Get minimal fields first (just ID and subject)
    select_params_minimal = SelectParams(
        id=True,
        subject=True
    )

    result_list = await mail_service.query_mail_list(
        user_email=user_email,
        query_method=QueryMethod.FILTER,
        filter_params=filter_params,
        select_params=select_params_minimal,
        top=5
    )

    if not result_list.get("success"):
        print(f"❌ Failed to get mail list: {result_list.get('error')}")
        return

    emails = result_list.get("emails", [])
    print(f"✅ Found {len(emails)} emails")

    if not emails:
        print("❌ No emails to test with")
        return

    # Extract mail IDs
    mail_ids = [email['id'] for email in emails if email.get('id')]

    print(f"\n📋 Mail IDs collected:")
    for i, mail_id in enumerate(mail_ids[:3], 1):
        print(f"  {i}. {mail_id[:50]}...")

    # Step 2: Test mail_query_with_ID (batch_and_fetch)
    print("\n" + "=" * 60)
    print("📧 Step 2: Testing mail_query_with_ID (batch_and_fetch)")
    print("-" * 40)

    # Test with first 3 mail IDs
    test_ids = mail_ids[:3]
    print(f"\n🔄 Fetching {len(test_ids)} emails by ID...")

    # Call batch_and_fetch directly (simulating mail_query_with_ID)
    batch_result = await mail_service.batch_and_fetch(
        user_email=user_email,
        message_ids=test_ids,
        select_params=SelectParams(
            id=True,
            subject=True,
            body_preview=True,
            sender=True,
            received_date_time=True,
            has_attachments=True
        )
    )

    # Check results
    if batch_result.get("success") or "value" in batch_result:
        batch_emails = batch_result.get("value", batch_result.get("emails", []))
        print(f"\n✅ Successfully fetched {len(batch_emails)} emails by ID")

        print("\n📊 Fetched Email Details:")
        print("-" * 40)

        for i, email in enumerate(batch_emails, 1):
            print(f"\nEmail {i}:")
            print(f"  ID: {email.get('id', 'N/A')[:50]}...")
            print(f"  Subject: {email.get('subject', 'N/A')}")

            sender_info = email.get('sender', {})
            if sender_info:
                sender_email = sender_info.get('emailAddress', {}).get('address', 'N/A')
            else:
                sender_email = 'N/A'
            print(f"  From: {sender_email}")

            print(f"  Date: {email.get('receivedDateTime', 'N/A')}")
            print(f"  Has Attachments: {email.get('hasAttachments', 'N/A')}")

            preview = email.get('bodyPreview', '')[:100]
            if preview:
                print(f"  Preview: {preview}...")

        # Verify IDs match
        print("\n🔍 ID Verification:")
        fetched_ids = [e.get('id') for e in batch_emails if e.get('id')]

        for test_id in test_ids:
            if test_id in fetched_ids:
                print(f"  ✅ ID found: {test_id[:30]}...")
            else:
                print(f"  ❌ ID missing: {test_id[:30]}...")

    else:
        print(f"\n❌ Failed to fetch emails by ID")
        print(f"Error: {batch_result.get('error', 'Unknown error')}")
        if batch_result.get('details'):
            print(f"Details: {json.dumps(batch_result.get('details'), indent=2)}")

    # Step 3: Test with comma-separated string (as the handler expects)
    print("\n" + "=" * 60)
    print("📧 Step 3: Testing with comma-separated ID string")
    print("-" * 40)

    # Simulate what the REST API would receive
    ids_string = ",".join(test_ids[:2])  # Test with 2 IDs as comma-separated
    print(f"\n🔄 Testing with IDs string: {ids_string[:100]}...")

    # Simulate the handler logic
    message_ids = [id.strip() for id in ids_string.split(",") if id.strip()]

    batch_result2 = await mail_service.batch_and_fetch(
        user_email=user_email,
        message_ids=message_ids,
        select_params=None  # Use default params
    )

    if batch_result2.get("success") or "value" in batch_result2:
        batch_emails2 = batch_result2.get("value", batch_result2.get("emails", []))
        print(f"\n✅ Successfully fetched {len(batch_emails2)} emails with comma-separated IDs")

        for email in batch_emails2:
            print(f"  - {email.get('subject', 'N/A')[:50]}...")
    else:
        print(f"\n❌ Failed with comma-separated IDs: {batch_result2.get('error')}")

    # Cleanup
    if hasattr(mail_service, '_client') and mail_service._client:
        await mail_service._client.close()

    print("\n" + "=" * 60)
    print("✅ Test completed")

async def main():
    await test_mail_query_with_id()

if __name__ == "__main__":
    asyncio.run(main())