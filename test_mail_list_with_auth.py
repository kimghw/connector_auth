#!/usr/bin/env python3
"""
Test script for mail_list handler with automatic authentication
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

# Import required modules
from mcp_outlook.mail_service import MailService
from mcp_outlook.outlook_types import FilterParams, SelectParams
from mcp_outlook.graph_mail_client import QueryMethod
from session.auth_manager import AuthManager

async def get_authenticated_user():
    """
    Get authenticated user from session
    """
    auth_manager = AuthManager()

    # Get all stored tokens
    all_tokens = await auth_manager.get_all_tokens()

    if not all_tokens:
        print("❌ No authenticated users found in session")
        print("Please authenticate first using the OAuth flow")
        return None

    # Use the first available user or specific user
    for user_email, token_data in all_tokens.items():
        if token_data.get('access_token'):
            print(f"✅ Found authenticated user: {user_email}")
            return user_email

    print("❌ No valid access tokens found")
    return None

async def ensure_token_valid(user_email: str):
    """
    Ensure the token is valid, refresh if needed
    """
    auth_manager = AuthManager()

    # This will refresh the token if needed
    access_token = await auth_manager.validate_and_refresh_token(user_email)

    if access_token:
        print(f"✅ Token validated for {user_email}")
        return True
    else:
        print(f"❌ Failed to validate token for {user_email}")
        return False

async def test_mail_list():
    """
    Test the mail_list (query_mail_list) handler
    """
    print("=" * 60)
    print("Testing mail_list handler with authentication")
    print("=" * 60)

    # Get authenticated user
    user_email = await get_authenticated_user()

    if not user_email:
        print("\n⚠️  No authenticated user found")
        print("Please run the authentication flow first:")
        print("  python session/auth_flow.py")
        return

    # Ensure token is valid
    if not await ensure_token_valid(user_email):
        print("\n⚠️  Token validation failed")
        print("Please re-authenticate:")
        print("  python session/auth_flow.py")
        return

    # Initialize the mail service
    mail_service = MailService()
    await mail_service.initialize()
    print("\n✅ Mail service initialized")

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
    top = 10  # Limit to 10 emails for testing

    print(f"\n📧 Testing with authenticated user: {user_email}")
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

                # Safely get sender email
                sender_info = email.get('sender', {})
                if sender_info:
                    sender_email = sender_info.get('emailAddress', {}).get('address', 'N/A')
                else:
                    sender_email = 'N/A'
                print(f"  From: {sender_email}")

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

            # Test specific mail_list features
            print(f"\n🧪 Mail List Specific Features:")
            print(f"  - User: {result.get('user', 'N/A')}")
            print(f"  - Total emails found: {len(emails)}")

            if emails and len(emails) > 0:
                # Check if the expected fields are present
                first_email = emails[0]
                expected_fields = ['id', 'subject', 'bodyPreview', 'receivedDateTime', 'sender', 'hasAttachments']
                present_fields = [f for f in expected_fields if f in first_email]
                missing_fields = [f for f in expected_fields if f not in first_email]

                print(f"  - Present fields: {', '.join(present_fields)}")
                if missing_fields:
                    print(f"  - Missing fields: {', '.join(missing_fields)}")

        else:
            print(f"\n❌ Failed to retrieve mail list")
            print(f"Error: {result.get('error', 'Unknown error')}")
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