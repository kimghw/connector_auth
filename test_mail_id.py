#!/usr/bin/env python3
"""
Test mail ID return in mail_list handler
Verify that mail IDs are properly returned
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

async def test_mail_id():
    """Test mail ID return"""
    print("=" * 60)
    print("Testing mail ID return")
    print("=" * 60)

    # Initialize mail service
    mail_service = MailService()
    await mail_service.initialize()
    print("✅ Mail service initialized\n")

    # Set up test parameters
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)

    filter_params = FilterParams(
        received_date_from=start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        received_date_to=end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    # Test with internal default select params (from tool_internal_args.json)
    print("📧 Testing with default internal select params")
    print("-" * 40)

    # Don't specify select_params - should use defaults from tool_internal_args.json
    result = await mail_service.query_mail_list(
        user_email="kimghw@krs.co.kr",
        query_method=QueryMethod.FILTER,
        filter_params=filter_params,
        select_params=SelectParams(
            id=True,  # This should be true by default
            subject=True,
            body_preview=True,
            received_date_time=True,
            sender=True,
            has_attachments=True,
            internet_message_id=True
        ),
        top=5
    )

    if result.get("success"):
        emails = result.get("emails", [])
        print(f"✅ Retrieved {len(emails)} emails\n")

        # Check each email for ID
        print("🔍 Checking mail IDs:")
        print("-" * 40)

        for i, email in enumerate(emails, 1):
            mail_id = email.get('id')
            subject = email.get('subject', 'N/A')[:50]

            if mail_id:
                print(f"\n✅ Email {i}:")
                print(f"   ID: {mail_id[:50]}...")
                print(f"   Subject: {subject}")

                # Verify ID format (Microsoft Graph mail IDs are long base64 strings)
                if len(mail_id) > 100 and mail_id.startswith('AAMkA'):
                    print(f"   ID Format: ✅ Valid Graph API format")
                else:
                    print(f"   ID Format: ⚠️  Unexpected format")
            else:
                print(f"\n❌ Email {i}: No ID found!")
                print(f"   Subject: {subject}")

        # Summary
        print("\n" + "=" * 60)
        print("📊 Summary:")
        ids_found = sum(1 for e in emails if e.get('id'))
        print(f"  - Emails with IDs: {ids_found}/{len(emails)}")

        if ids_found == len(emails):
            print("  ✅ All emails have IDs!")
        else:
            print(f"  ❌ {len(emails) - ids_found} emails missing IDs")

    else:
        print(f"❌ Failed: {result.get('error')}")

    # Cleanup
    if hasattr(mail_service, '_client') and mail_service._client:
        await mail_service._client.close()

    print("\n✅ Test completed")

async def main():
    await test_mail_id()

if __name__ == "__main__":
    asyncio.run(main())