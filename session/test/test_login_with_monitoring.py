#!/usr/bin/env python3
"""
로그인 테스트 스크립트 - 각 단계마다 DB 상태 모니터링
"""

import asyncio
import sys
import os
import sqlite3
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import webbrowser
import time

# Load environment variables
load_dotenv()

# Add parent directories to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)
sys.path.insert(0, parent_dir)

from auth import AuthManager, AuthDatabase


def check_db_state(step_name: str, email: str = None):
    """DB 상태 확인 및 출력"""
    print(f"\n{'='*60}")
    print(f"📊 DB 상태 확인 - {step_name}")
    print(f"{'='*60}")

    conn = sqlite3.connect("database/auth.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. 사용자 정보 확인
        print("\n[1] 사용자 정보 (azure_user_info):")
        print("-" * 50)

        if email:
            cursor.execute("SELECT * FROM azure_user_info WHERE user_email = ?", (email,))
        else:
            cursor.execute("SELECT * FROM azure_user_info ORDER BY updated_at DESC LIMIT 5")

        users = cursor.fetchall()
        if users:
            for user in users:
                print(f"  Email: {user['user_email']}")
                print(f"  Name: {user['display_name']}")
                print(f"  Object ID: {user['object_id']}")
                print(f"  Created: {user['created_at']}")
                print(f"  Updated: {user['updated_at']}")
                print("-" * 50)
        else:
            print("  ❌ 사용자 정보 없음")

        # 2. 토큰 정보 확인
        print("\n[2] 토큰 정보 (azure_token_info):")
        print("-" * 50)

        if email:
            cursor.execute("""
                SELECT user_email,
                       SUBSTR(access_token, 1, 20) || '...' as access_token_preview,
                       CASE WHEN refresh_token IS NOT NULL THEN '있음' ELSE '없음' END as refresh_status,
                       access_token_expires_at,
                       updated_at
                FROM azure_token_info
                WHERE user_email = ?
            """, (email,))
        else:
            cursor.execute("""
                SELECT user_email,
                       SUBSTR(access_token, 1, 20) || '...' as access_token_preview,
                       CASE WHEN refresh_token IS NOT NULL THEN '있음' ELSE '없음' END as refresh_status,
                       access_token_expires_at,
                       updated_at
                FROM azure_token_info
                ORDER BY updated_at DESC
                LIMIT 5
            """)

        tokens = cursor.fetchall()
        if tokens:
            for token in tokens:
                print(f"  Email: {token['user_email']}")
                print(f"  Access Token: {token['access_token_preview']}")
                print(f"  Refresh Token: {token['refresh_status']}")
                print(f"  Expires At: {token['access_token_expires_at']}")
                print(f"  Updated: {token['updated_at']}")

                # 만료 확인
                if token['access_token_expires_at']:
                    expires_at = datetime.fromisoformat(
                        token['access_token_expires_at'].replace('Z', '+00:00')
                    )
                    now = datetime.now(timezone.utc)
                    if now >= expires_at:
                        print(f"  ⚠️ 토큰 만료됨!")
                    else:
                        remaining = expires_at - now
                        print(f"  ✅ 토큰 유효 (남은 시간: {remaining})")
                print("-" * 50)
        else:
            print("  ❌ 토큰 정보 없음")

        # 3. 통계 정보
        print("\n[3] 전체 통계:")
        print("-" * 50)

        cursor.execute("SELECT COUNT(*) as count FROM azure_user_info")
        user_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM azure_token_info")
        token_count = cursor.fetchone()['count']

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM azure_token_info
            WHERE access_token_expires_at > datetime('now')
        """)
        valid_token_count = cursor.fetchone()['count']

        print(f"  전체 사용자 수: {user_count}")
        print(f"  전체 토큰 수: {token_count}")
        print(f"  유효한 토큰 수: {valid_token_count}")

    except Exception as e:
        print(f"❌ DB 조회 오류: {e}")
    finally:
        conn.close()


async def test_login_flow():
    """로그인 플로우 테스트 - 단계별 DB 모니터링"""

    print("\n" + "="*70)
    print("🔐 Azure AD 로그인 테스트 (DB 모니터링 포함)")
    print("="*70)

    auth_manager = AuthManager()

    try:
        # Step 1: 초기 상태 확인
        print("\n[Step 1] 초기 DB 상태 확인")
        check_db_state("초기 상태")

        # 기존 사용자 목록
        existing_users = auth_manager.list_users()
        existing_emails = {u['email'] for u in existing_users}
        print(f"\n현재 등록된 사용자: {len(existing_emails)}명")

        input("\n🔵 Enter를 눌러 로그인 시작...")

        # Step 2: 인증 URL 생성
        print("\n[Step 2] 인증 URL 생성 중...")
        auth_info = auth_manager.start_authentication()
        print(f"✅ 인증 URL 생성 완료")
        print(f"   State: {auth_info['state'][:20]}...")

        # 콜백 서버 시작
        print("\n[Step 3] 콜백 서버 시작...")
        await auth_manager.ensure_callback_server(port=5000)
        print("✅ 콜백 서버 실행 중 (http://localhost:5000)")

        # Step 4: 브라우저 열기
        print("\n[Step 4] 브라우저에서 인증 페이지 열기...")
        print(f"🌐 인증 URL: {auth_info['auth_url'][:100]}...")

        try:
            webbrowser.open(auth_info['auth_url'])
            print("✅ 브라우저 열림")
        except Exception as e:
            print(f"⚠️ 브라우저 자동 실행 실패: {e}")
            print(f"\n수동으로 접속: {auth_info['auth_url']}")

        # Step 5: 인증 대기
        print("\n[Step 5] 사용자 인증 대기 중...")
        print("⏳ 브라우저에서 로그인을 완료해주세요 (최대 5분)...")

        # 폴링 방식으로 새 사용자 또는 토큰 업데이트 확인
        start_time = asyncio.get_event_loop().time()
        timeout = 300  # 5분
        authenticated_email = None

        # 기존 사용자들의 토큰 업데이트 시간 저장
        existing_token_times = {}
        for user in existing_users:
            token = auth_manager.auth_db.get_token(user['email'])
            if token:
                existing_token_times[user['email']] = token.get('updated_at')

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            await asyncio.sleep(2)  # 2초마다 확인

            current_users = auth_manager.list_users()
            current_emails = {u['email'] for u in current_users}

            # 1. 새로운 사용자가 추가되었는지 확인
            new_emails = current_emails - existing_emails
            if new_emails:
                authenticated_email = list(new_emails)[0]
                print(f"\n✅ 새 사용자 인증 완료: {authenticated_email}")
                break

            # 2. 기존 사용자의 토큰이 업데이트되었는지 확인
            for email in current_emails:
                token = auth_manager.auth_db.get_token(email)
                if token:
                    current_update_time = token.get('updated_at')
                    if email in existing_token_times:
                        if current_update_time != existing_token_times[email]:
                            authenticated_email = email
                            print(f"\n✅ 기존 사용자 재인증 완료: {authenticated_email}")
                            break
                    else:
                        # 새로운 토큰이 생성된 경우
                        authenticated_email = email
                        print(f"\n✅ 토큰 생성 완료: {authenticated_email}")
                        break

            if authenticated_email:
                break

            # 진행 상황 표시
            elapsed = int(asyncio.get_event_loop().time() - start_time)
            print(f"  ⏱️ 대기 중... ({elapsed}초)", end='\r')

        if not authenticated_email:
            print("\n❌ 인증 시간 초과")
            return

        # Step 6: 인증 직후 DB 상태 확인
        print("\n[Step 6] 인증 직후 DB 상태")
        await asyncio.sleep(1)  # DB 쓰기 대기
        check_db_state("인증 완료 직후", authenticated_email)

        # Step 7: 토큰 정보 조회
        print("\n[Step 7] 토큰 정보 조회 테스트")
        token_info = await auth_manager.get_token(authenticated_email)

        if token_info:
            print(f"✅ 토큰 조회 성공")
            print(f"   Email: {token_info['email']}")
            print(f"   만료 여부: {'만료됨' if token_info['is_expired'] else '유효함'}")
            print(f"   Refresh Token: {'있음' if token_info.get('refresh_token') else '없음'}")
            print(f"   만료 시간: {token_info['expires_at']}")
        else:
            print("❌ 토큰 조회 실패")

        # Step 8: 토큰 갱신 테스트 (refresh token이 있는 경우)
        if token_info and token_info.get('refresh_token'):
            input("\n🔵 Enter를 눌러 토큰 갱신 테스트...")

            print("\n[Step 8] 토큰 갱신 테스트")
            refresh_result = await auth_manager.refresh_token(authenticated_email)

            if refresh_result['status'] == 'success':
                print(f"✅ 토큰 갱신 성공")
                print(f"   새 만료 시간: {refresh_result['expires_at']}")

                # 갱신 후 DB 상태 확인
                print("\n[Step 9] 토큰 갱신 후 DB 상태")
                await asyncio.sleep(1)  # DB 쓰기 대기
                check_db_state("토큰 갱신 후", authenticated_email)
            else:
                print(f"❌ 토큰 갱신 실패: {refresh_result.get('error')}")

        # Step 10: 최종 통계
        print("\n[Step 10] 최종 상태 요약")
        print("="*60)

        all_users = auth_manager.list_users()
        valid_users = [u for u in all_users if not u.get('token_expired', True)]

        print(f"📊 전체 사용자: {len(all_users)}명")
        print(f"✅ 유효한 토큰 보유: {len(valid_users)}명")
        print(f"⚠️ 만료된 토큰: {len(all_users) - len(valid_users)}명")

        print("\n등록된 사용자 목록:")
        for user in all_users:
            status = "✅" if not user.get('token_expired', True) else "⚠️"
            print(f"  {status} {user['email']} - {user.get('display_name', 'N/A')}")

    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 정리
        await auth_manager.close()
        print("\n✅ 테스트 완료 - 리소스 정리됨")


if __name__ == "__main__":
    print("Azure AD 로그인 테스트 시작...")
    print("이 스크립트는 각 단계마다 DB 상태를 모니터링합니다.")
    asyncio.run(test_login_flow())