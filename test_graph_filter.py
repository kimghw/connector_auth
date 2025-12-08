#!/usr/bin/env python3
"""
Graph API 필터 테스트 - ne 연산자 동작 확인
"""
import asyncio
import aiohttp
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from auth.auth_manager import AuthManager


async def test_graph_api_filters():
    """Graph API의 여러 필터 테스트"""

    auth_manager = AuthManager()
    users = auth_manager.list_users()

    if not users:
        print("❌ No authenticated users")
        return

    user_email = users[0]['email']
    access_token = await auth_manager.validate_and_refresh_token(user_email)

    if not access_token:
        print("❌ Failed to get access token")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    base_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages"

    # 최근 3일 날짜
    date_from = datetime.now(timezone.utc) - timedelta(days=3)
    date_filter = f"receivedDateTime ge {date_from.strftime('%Y-%m-%dT%H:%M:%SZ')}"

    # 테스트 케이스들
    test_cases = [
        {
            "name": "날짜 필터만",
            "filter": date_filter,
            "expect_block": True
        },
        {
            "name": "날짜 + ne 연산자 (단일)",
            "filter": f"{date_filter} and from/emailAddress/address ne 'block@krs.co.kr'",
            "expect_block": False
        },
        {
            "name": "날짜 + not eq 연산자",
            "filter": f"{date_filter} and not (from/emailAddress/address eq 'block@krs.co.kr')",
            "expect_block": False
        }
    ]

    async with aiohttp.ClientSession() as session:
        for test in test_cases:
            print(f"\n📧 테스트: {test['name']}")
            print(f"   Filter: {test['filter']}")

            url = f"{base_url}?$filter={test['filter']}&$top=20&$select=from,subject"

            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        emails = data.get('value', [])

                        # block@krs.co.kr 메일 개수 카운트
                        block_count = 0
                        for email in emails:
                            sender = email.get('from', {}).get('emailAddress', {}).get('address', '')
                            if sender == 'block@krs.co.kr':
                                block_count += 1

                        print(f"   결과: 총 {len(emails)}개 메일, block@krs.co.kr: {block_count}개")

                        if test['expect_block'] and block_count == 0:
                            print(f"   ⚠️ 예상과 다름: block@krs.co.kr이 포함되어야 함")
                        elif not test['expect_block'] and block_count > 0:
                            print(f"   ❌ 실패: block@krs.co.kr이 제외되어야 함 (ne 연산자 작동 안함)")
                        else:
                            print(f"   ✅ 성공")

                    else:
                        error_text = await response.text()
                        print(f"   ❌ API 오류 {response.status}: {error_text[:200]}")

            except Exception as e:
                print(f"   ❌ 예외 발생: {str(e)}")

    await auth_manager.close()


if __name__ == "__main__":
    asyncio.run(test_graph_api_filters())