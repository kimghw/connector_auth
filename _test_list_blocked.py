"""test list_blocked action"""
import asyncio
import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_outlook.outlook_service import MailService

async def main():
    svc = MailService()
    await svc.initialize()
    try:
        result = await svc.mail_action(
            user_email="kimghw@krs.co.kr",
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
