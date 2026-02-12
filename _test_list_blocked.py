"""test list_blocked action"""
import asyncio
import sys
import os
import io
from typing import Optional
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_outlook.outlook_service import MailService
from session.auth_database import AuthDatabase


def get_default_user_email() -> Optional[str]:
    """auth.db에서 첫 번째 사용자 이메일을 가져옴"""
    db = AuthDatabase()
    users = db.list_users()
    if users:
        return users[0].get('user_email')
    return None


async def main():
    # user_email이 없으면 DB에서 가져옴
    user_email = get_default_user_email()
    if not user_email:
        print("[ERROR] No authenticated user found in database")
        return

    svc = MailService()
    await svc.initialize()
    try:
        result = await svc.mail_action(
            user_email=user_email,
            message_ids=[],
            action="list_blocked",
            destination_id="1",
        )
        emails = result.get("emails", [])
        print(f"Total: {len(emails)} mails from block@krs.co.kr\n")
        for i, mail in enumerate(emails, 1):
            subj = mail.get("subject", "(no subject)")
            from_addr = (mail.get("from") or mail.get("sender", {})).get("emailAddress", {}).get("address", "?")
            recv = mail.get("receivedDateTime", "?")[:16]
            mail_id = mail.get("id", "?")[:20]
            print(f"  {i}. [{recv}] {subj}")
    finally:
        await svc.close()

asyncio.run(main())
