#!/usr/bin/env python3
"""
Test script for mail_list handler
Tests the query_mail_list function with automatic token generation from session
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the mail service
from mcp_outlook.mail_service import MailService
from mcp_outlook.outlook_types import FilterParams, SelectParams
from mcp_outlook.graph_mail_client import QueryMethod

async def test_mail_list():
    """
    Test the mail_list (query_mail_list) handler
    """
    print("=" * 60)
    print("Testing mail_list handler")
    print("=" * 60)

    # Initialize the mail service
    mail_service = MailService()
    await mail_service.initialize()
    print("✅ Mail service initialized")

    # Set up test parameters
    # Calculate date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # Format dates for Graph API (ISO 8601 format)
    date_from = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_to = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"\n📅 Date range: {date_from} to {date_to}")

    # Create filter parameters
    filter_params = FilterParams(
        received_date_from=date_from,
        received_date_to=date_to
    )

    # Create select parameters (specify which fields to retrieve)
    select_params = SelectParams(
        id=True,
        subject=True,
        body_preview=True,
        received_date_time=True,
        sender=True,
        has_attachments=True,
        internet_message_id=True
    )

    # Test parameters
    user_email = "kimghw@krs.co.kr"  # Testing with specific user
    top = 10  # Limit to 10 emails for testing

    print(f"\n📧 Testing with user: {user_email}")
    print(f"📊 Retrieving top {top} emails")

    try:
        # Call the query_mail_list function
        print("\n🔄 Calling query_mail_list...")
        result = await mail_service.query_mail_list(
            user_email=user_email,
            query_method=QueryMethod.FILTER,
            filter_params=filter_params,
            select_params=select_params,
            top=top,
            order_by="receivedDateTime desc"
        )

        # Check if successful
        if result.get("success"):
            print("\n✅ Successfully retrieved mail list!")

            # Display results
            emails = result.get("emails", [])
            print(f"\n📬 Found {len(emails)} emails")

            # Show summary of each email
            for i, email in enumerate(emails[:5], 1):  # Show first 5
                print(f"\n--- Email {i} ---")
                print(f"  Subject: {email.get('subject', 'N/A')}")
                print(f"  From: {email.get('sender', {}).get('emailAddress', {}).get('address', 'N/A')}")
                print(f"  Date: {email.get('receivedDateTime', 'N/A')}")
                print(f"  Has Attachments: {email.get('hasAttachments', False)}")
                preview = email.get('bodyPreview', '')[:100]
                if preview:
                    print(f"  Preview: {preview}...")

            # Show statistics
            if emails:
                print(f"\n📊 Statistics:")
                with_attachments = sum(1 for e in emails if e.get('hasAttachments'))
                print(f"  - Emails with attachments: {with_attachments}/{len(emails)}")

                # Parse dates and find range
                dates = []
                for email in emails:
                    date_str = email.get('receivedDateTime')
                    if date_str:
                        try:
                            dates.append(datetime.fromisoformat(date_str.replace('Z', '+00:00')))
                        except:
                            pass

                if dates:
                    oldest = min(dates)
                    newest = max(dates)
                    print(f"  - Date range in results: {oldest.strftime('%Y-%m-%d')} to {newest.strftime('%Y-%m-%d')}")

            # Show query details
            print(f"\n🔍 Query Details:")
            print(f"  - Method: {result.get('method', 'N/A')}")
            if result.get('filter_query'):
                print(f"  - Filter: {result.get('filter_query')}")
            if result.get('select_fields'):
                print(f"  - Selected fields: {', '.join(result.get('select_fields', []))}")
            print(f"  - Order by: {result.get('order_by', 'N/A')}")

        else:
            print(f"\n❌ Failed to retrieve mail list")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Full result: {json.dumps(result, indent=2)}")
            if result.get('details'):
                print(f"Details: {json.dumps(result.get('details'), indent=2)}")

    except Exception as e:
        print(f"\n❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if hasattr(mail_service, '_client') and mail_service._client:
            await mail_service._client.close()
        print("\n✅ Cleanup completed")

async def main():
    """Main function"""
    await test_mail_list()
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())