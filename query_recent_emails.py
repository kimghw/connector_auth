#!/usr/bin/env python3
"""
최근 3일간 수신한 메일 조회 스크립트
block@krs.co.kr 제외
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

# 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.auth_manager import AuthManager
from mcp_outlook.graph_mail_query import GraphMailQuery
from mcp_outlook.graph_types import (
    FilterParams,
    ExcludeParams,
    SelectParams,
    create_filter_params,
    create_exclude_params,
    create_select_params
)


async def query_recent_emails_excluding_blocked(
    days_back: int = 3,
    blocked_email: str = "block@krs.co.kr",
    user_email: Optional[str] = None,
    max_emails: int = 450
) -> Dict[str, Any]:
    """
    최근 N일간 수신한 메일 조회 (특정 이메일 제외)

    Args:
        days_back: 조회할 최근 일수 (기본 3일)
        blocked_email: 제외할 이메일 주소
        user_email: 사용자 이메일 (None이면 첫 번째 인증된 사용자)
        max_emails: 최대 조회 메일 수

    Returns:
        조회 결과
    """

    # 3일 전 날짜 계산 (UTC 기준)
    date_from = datetime.now(timezone.utc) - timedelta(days=days_back)
    date_from_iso = date_from.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"📧 최근 {days_back}일간 수신 메일 조회 중...")
    print(f"   기준 날짜: {date_from_iso}")
    print(f"   제외 발신자: {blocked_email}")
    print("-" * 80)

    # Graph Mail Query 초기화
    query = GraphMailQuery(user_email=user_email)

    try:
        # 초기화
        if not await query.initialize():
            print("❌ 초기화 실패")
            return {"status": "error", "message": "Failed to initialize"}

        print(f"✅ 인증 완료: {query.user_email}")

        # 필터 파라미터 생성 (포함 조건)
        filter_params: FilterParams = create_filter_params(
            received_date_time=date_from_iso  # 최근 3일 이내
        )

        # 제외 파라미터 생성 (제외 조건)
        exclude_params: ExcludeParams = create_exclude_params(
            exclude_from_address=blocked_email  # block@krs.co.kr 제외
        )

        # 선택 필드 설정 (필요한 필드만 가져오기)
        select_params: SelectParams = create_select_params(
            fields=[
                "id",
                "subject",
                "from",
                "receivedDateTime",
                "hasAttachments",
                "importance",
                "isRead",
                "bodyPreview"
            ]
        )

        # 쿼리 실행
        print(f"\n📥 메일 조회 중 (최대 {max_emails}개)...")

        # Graph API filter가 ne 연산자를 제대로 처리하지 못하는 경우가 있으므로
        # client-side filtering 사용
        result = await query.query_filter(
            filter=filter_params,
            exclude=None,  # Server-side exclude 사용 안함
            select=select_params,
            client_filter=exclude_params,  # Client-side filtering 사용
            top=max_emails,
            orderby="receivedDateTime desc"  # 최신 메일 우선
        )

        # 결과 처리
        if result.get('status') == 'success' or 'value' in result:
            emails = result.get('emails') or result.get('value', [])

            print(f"\n✅ 조회 완료: 총 {len(emails)}개 메일")
            print("=" * 80)

            # 메일 정보 출력
            for idx, email in enumerate(emails, 1):
                # 날짜 포맷팅
                received_dt = email.get('receivedDateTime', 'Unknown')
                if received_dt != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(received_dt.replace('Z', '+00:00'))
                        received_dt_formatted = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        received_dt_formatted = received_dt
                else:
                    received_dt_formatted = 'Unknown'

                # 발신자 정보
                from_info = email.get('from', {})
                sender_name = from_info.get('emailAddress', {}).get('name', 'Unknown')
                sender_email = from_info.get('emailAddress', {}).get('address', 'Unknown')

                # 메일 상태
                subject = email.get('subject', 'No Subject')
                is_read = email.get('isRead', False)
                has_attachments = email.get('hasAttachments', False)
                importance = email.get('importance', 'normal')
                preview = email.get('bodyPreview', '')[:100]

                # 상태 아이콘
                read_icon = "📖" if is_read else "✉️"
                attach_icon = "📎" if has_attachments else ""
                imp_icon = "❗" if importance == 'high' else ""

                # 출력
                print(f"\n[{idx}] {read_icon} {imp_icon}{attach_icon} {subject}")
                print(f"     From: {sender_name} <{sender_email}>")
                print(f"     Date: {received_dt_formatted}")
                if preview:
                    print(f"     Preview: {preview}...")

            print("\n" + "=" * 80)

            # 통계
            unread_count = len([e for e in emails if not e.get('isRead', False)])
            with_attachments = len([e for e in emails if e.get('hasAttachments', False)])
            high_importance = len([e for e in emails if e.get('importance') == 'high'])

            print(f"\n📊 통계:")
            print(f"   - 총 메일: {len(emails)}개")
            print(f"   - 읽지 않은 메일: {unread_count}개")
            print(f"   - 첨부파일 있는 메일: {with_attachments}개")
            print(f"   - 중요도 높음: {high_importance}개")

            return {
                "status": "success",
                "emails": emails,
                "statistics": {
                    "total": len(emails),
                    "unread": unread_count,
                    "with_attachments": with_attachments,
                    "high_importance": high_importance
                }
            }
        else:
            print(f"❌ 조회 실패: {result.get('error', 'Unknown error')}")
            return result

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        await query.close()


async def main():
    """메인 함수"""

    # AuthManager로 인증 상태 확인
    auth_manager = AuthManager()
    users = auth_manager.list_users()

    if not users:
        print("⚠️ 인증된 사용자가 없습니다.")
        print("먼저 인증을 진행해주세요:")
        print("  python -m auth.auth_cli authenticate")
        await auth_manager.close()
        return

    print("📧 인증된 사용자 목록:")
    for idx, user in enumerate(users, 1):
        token_status = "✅" if not user.get('token_expired', True) else "⚠️ (토큰 만료)"
        print(f"  [{idx}] {user['email']} {token_status}")

    # 첫 번째 사용자 선택
    selected_user = users[0]['email']
    print(f"\n선택된 사용자: {selected_user}")
    print("-" * 80)

    await auth_manager.close()

    # 메일 조회 실행
    result = await query_recent_emails_excluding_blocked(
        days_back=3,
        blocked_email="block@krs.co.kr",
        user_email=selected_user,
        max_emails=450
    )

    # 결과를 JSON 파일로 저장 (선택사항)
    if result.get('status') == 'success' and result.get('emails'):
        import json
        output_file = f"recent_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "query_date": datetime.now().isoformat(),
                "days_back": 3,
                "excluded_sender": "block@krs.co.kr",
                "user_email": selected_user,
                "statistics": result.get('statistics'),
                "email_count": len(result['emails']),
                "emails": result['emails']
            }, f, ensure_ascii=False, indent=2)

        print(f"\n💾 결과가 {output_file}에 저장되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())