#!/usr/bin/env python3
"""
Test select_params functionality in mail_list handler
Verifies that field selection is working correctly
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

async def test_select_params():
    """
    Test select_params with different field selections
    """
    print("=" * 60)
    print("Testing select_params functionality")
    print("=" * 60)

    # Initialize mail service
    mail_service = MailService()
    await mail_service.initialize()
    print("✅ Mail service initialized\n")

    # Set up date range (last 3 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    date_from = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_to = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    filter_params = FilterParams(
        received_date_from=date_from,
        received_date_to=date_to
    )

    user_email = "kimghw@krs.co.kr"
    top = 3  # Get only 3 emails for testing

    # Test 1: Minimal fields (only id and subject)
    print("📧 Test 1: Minimal fields (id, subject only)")
    print("-" * 40)

    select_params_minimal = SelectParams(
        id=True,
        subject=True
    )

    result1 = await mail_service.query_mail_list(
        user_email=user_email,
        query_method=QueryMethod.FILTER,
        filter_params=filter_params,
        select_params=select_params_minimal,
        top=top
    )

    if result1.get("success"):
        emails = result1.get("emails", [])
        print(f"✅ Retrieved {len(emails)} emails")

        if emails:
            first_email = emails[0]
            print(f"\nFields in first email:")
            for field in sorted(first_email.keys()):
                print(f"  - {field}")

            # Check if only requested fields are present
            expected_fields = {'id', 'subject', '@odata.etag'}  # @odata.etag is always included
            actual_fields = set(first_email.keys())
            extra_fields = actual_fields - expected_fields
            missing_fields = expected_fields - actual_fields - {'@odata.etag'}

            if extra_fields:
                print(f"\n⚠️  Extra fields returned: {extra_fields}")
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
            if not extra_fields and not missing_fields:
                print(f"\n✅ Only requested fields returned!")
    else:
        print(f"❌ Test 1 failed: {result1.get('error')}")

    print("\n" + "=" * 60)

    # Test 2: All available fields
    print("📧 Test 2: All available fields")
    print("-" * 40)

    select_params_full = SelectParams(
        id=True,
        subject=True,
        body_preview=True,
        received_date_time=True,
        sent_date_time=True,
        created_date_time=True,
        sender=True,
        from_recipient=True,
        has_attachments=True,
        internet_message_id=True,
        importance=True,
        is_read=True,
        categories=True,
        flag=True
    )

    result2 = await mail_service.query_mail_list(
        user_email=user_email,
        query_method=QueryMethod.FILTER,
        filter_params=filter_params,
        select_params=select_params_full,
        top=top
    )

    if result2.get("success"):
        emails = result2.get("emails", [])
        print(f"✅ Retrieved {len(emails)} emails")

        if emails:
            first_email = emails[0]
            print(f"\nFields in first email:")
            fields_count = 0
            for field in sorted(first_email.keys()):
                if not field.startswith('@odata'):
                    print(f"  - {field}")
                    fields_count += 1

            print(f"\nTotal fields (excluding @odata): {fields_count}")

            # Check specific fields
            print("\nField values check:")
            print(f"  - subject: {first_email.get('subject', 'N/A')[:50]}...")
            print(f"  - hasAttachments: {first_email.get('hasAttachments', 'N/A')}")
            print(f"  - isRead: {first_email.get('isRead', 'N/A')}")
            print(f"  - importance: {first_email.get('importance', 'N/A')}")

            if first_email.get('sender'):
                sender_email = first_email['sender'].get('emailAddress', {}).get('address', 'N/A')
                print(f"  - sender: {sender_email}")
    else:
        print(f"❌ Test 2 failed: {result2.get('error')}")

    print("\n" + "=" * 60)

    # Test 3: No select_params (should return default fields)
    print("📧 Test 3: No select_params (default fields)")
    print("-" * 40)

    result3 = await mail_service.query_mail_list(
        user_email=user_email,
        query_method=QueryMethod.FILTER,
        filter_params=filter_params,
        select_params=None,  # No selection
        top=top
    )

    if result3.get("success"):
        emails = result3.get("emails", [])
        print(f"✅ Retrieved {len(emails)} emails")

        if emails:
            first_email = emails[0]
            print(f"\nDefault fields returned:")
            for field in sorted(first_email.keys()):
                if not field.startswith('@odata'):
                    print(f"  - {field}")

            field_count = len([f for f in first_email.keys() if not f.startswith('@odata')])
            print(f"\nTotal default fields: {field_count}")
    else:
        print(f"❌ Test 3 failed: {result3.get('error')}")

    # Compare query strings
    print("\n" + "=" * 60)
    print("🔍 Query Analysis")
    print("-" * 40)

    if result1.get('select_fields'):
        print(f"Test 1 select fields: {', '.join(result1['select_fields'])}")
    if result2.get('select_fields'):
        print(f"Test 2 select fields: {', '.join(result2['select_fields'][:5])}... ({len(result2['select_fields'])} total)")
    if result3.get('select_fields'):
        print(f"Test 3 select fields: {', '.join(result3['select_fields'])}")
    else:
        print("Test 3: No select fields (all fields returned)")

    # Cleanup
    if hasattr(mail_service, '_client') and mail_service._client:
        await mail_service._client.close()

    print("\n✅ Test completed")

async def main():
    await test_select_params()

if __name__ == "__main__":
    asyncio.run(main())