#!/usr/bin/env python3
"""
Mail Text Processor 테스트
메일과 첨부파일의 텍스트 통합 처리 테스트 스크립트
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from outlook_mcp.mail_text_processor import MailTextProcessor
from auth.auth_manager import AuthManager


async def test_integration():
    """통합 테스트"""
    print("\n" + "=" * 70)
    print("Mail-Attachment Integration Test")
    print("=" * 70)

    # 1. 인증
    print("\n1. 인증 확인")
    auth_manager = AuthManager()
    users = auth_manager.list_users()

    if not users:
        print("❌ 인증된 사용자가 없습니다.")
        print("먼저 인증을 진행하세요: python -m auth.auth_cli authenticate")
        await auth_manager.close()
        return

    user_email = users[0]['email']
    print(f"✅ 사용자: {user_email}")

    # 토큰 가져오기
    access_token = await auth_manager.validate_and_refresh_token(user_email)
    if not access_token:
        print("❌ 액세스 토큰을 가져올 수 없습니다.")
        await auth_manager.close()
        return

    print("✅ 액세스 토큰 획득")

    # 2. Processor 초기화
    print("\n2. Processor 초기화")
    processor = MailTextProcessor(access_token)
    await processor.initialize()
    print("✅ 초기화 완료")

    # 3. 첨부파일이 있는 메일 찾기
    print("\n3. 첨부파일이 있는 최근 메일 검색")

    # 최근 7일간 첨부파일이 있는 메일 조회
    from outlook_mcp.graph_types import FilterParams
    filter_params: FilterParams = {
        'has_attachments': True,
        'received_date_from': (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
    }

    result = await processor.mail_query.query_filter(
        filter=filter_params,
        top=5  # 최대 5개만
    )

    if not result.get('emails'):
        print("❌ 첨부파일이 있는 메일을 찾을 수 없습니다.")
        await auth_manager.close()
        return

    mails = result['emails']
    print(f"✅ {len(mails)}개 메일 발견")

    for idx, mail in enumerate(mails[:3], 1):  # 최대 3개만 테스트
        print(f"\n[{idx}] {mail.get('subject', 'No Subject')}")
        print(f"    From: {mail.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')}")
        print(f"    Date: {mail.get('receivedDateTime', 'Unknown')[:10]}")

    # 4. 각 버전으로 처리 테스트
    test_mail = mails[0]
    mail_id = test_mail['id']

    print("\n" + "=" * 70)
    print(f"테스트 메일: {test_mail.get('subject', 'No Subject')}")
    print(f"메일 ID: {mail_id}")
    print("=" * 70)

    # 버전 1 테스트
    print("\n4. 버전 1 테스트 (단순 통합)")
    print("-" * 50)
    result_v1 = await processor.process_mail_v1_simple(mail_id)

    if result_v1.get('status') == 'success':
        print(f"✅ 성공!")
        print(f"   - 제목: {result_v1.get('subject')}")
        print(f"   - 첨부파일: {len(result_v1.get('attachments', []))}개")
        print(f"   - 통합 텍스트 길이: {result_v1.get('total_length', 0):,} 문자")

        # 첨부파일 정보
        for att in result_v1.get('attachments', []):
            if 'error' not in att:
                print(f"     📎 {att['name']} ({att['size']:,} bytes) → {att.get('text_length', 0):,} 문자")
            else:
                print(f"     ❌ {att['name']}: {att['error']}")

        # 통합 텍스트 미리보기
        combined = result_v1.get('combined_text', '')
        if combined:
            print(f"\n   통합 텍스트 미리보기 (처음 500자):")
            print("   " + "-" * 40)
            print(combined[:500])
    else:
        print(f"❌ 실패: {result_v1.get('error')}")

    # 버전 2 테스트
    print("\n5. 버전 2 테스트 (구조화된 통합)")
    print("-" * 50)
    result_v2 = await processor.process_mail_v2_structured(mail_id)

    if 'error' not in result_v2:
        print(f"✅ 성공!")
        summary = result_v2.get('summary', {})
        print(f"   - 총 첨부파일: {summary.get('total_attachments', 0)}개")
        print(f"   - 성공 변환: {summary.get('successful_conversions', 0)}개")
        print(f"   - 메일 텍스트: {summary.get('mail_text_length', 0):,} 문자")
        print(f"   - 첨부 텍스트: {summary.get('attachment_text_length', 0):,} 문자")
        print(f"   - 전체 텍스트: {summary.get('total_text_length', 0):,} 문자")

        # 메타데이터 확인
        for att in result_v2.get('attachments', []):
            if att.get('processing', {}).get('status') == 'success':
                print(f"\n   📎 {att['name']}")
                print(f"      - 추출 방법: {att.get('method', 'unknown')}")
                if att.get('metadata'):
                    print(f"      - 메타데이터: {list(att['metadata'].keys())}")
    else:
        print(f"❌ 실패: {result_v2.get('error')}")

    # 버전 3 테스트
    print("\n6. 버전 3 테스트 (분리 저장)")
    print("-" * 50)
    result_v3 = await processor.process_mail_v3_separated(mail_id, keep_files=True)

    if 'error' not in result_v3:
        print(f"✅ 성공!")
        print(f"   - 임시 디렉토리: {result_v3.get('temp_directory')}")

        files = result_v3.get('files', {})
        if files.get('mail'):
            print(f"   - 메일 파일: {Path(files['mail']).name}")

        if files.get('attachments'):
            print(f"   - 첨부파일: {len(files['attachments'])}개")
            for att_info in files['attachments']:
                print(f"     • {Path(att_info['original']).name}")
                print(f"       → {Path(att_info['text']).name}")

        if files.get('index'):
            print(f"   - 인덱스 파일: {Path(files['index']).name}")
    else:
        print(f"❌ 실패: {result_v3.get('error')}")

    # 7. 검색 테스트
    print("\n7. 검색 기능 테스트")
    print("-" * 50)

    # 여러 메일 처리
    print("여러 메일 처리 중...")
    mail_ids = [m['id'] for m in mails[:3]]  # 최대 3개
    batch_results = await processor.process_mail_batch(mail_ids, version="v2", parallel=True)

    # 키워드 검색
    test_keywords = ["the", "a", "to", "and", "회의", "계약", "첨부"]

    for keyword in test_keywords:
        search_results = await processor.search_in_processed_mails(keyword, batch_results)
        if search_results:
            print(f"\n✅ '{keyword}' 검색 결과: {len(search_results)}개 메일에서 발견")
            for sr in search_results[:2]:  # 최대 2개만 표시
                print(f"   📧 {sr['subject']}")
                for match in sr['matches'][:2]:  # 최대 2개 매치만 표시
                    print(f"      - {match['type']}: ...{match['context'][:100]}...")
            break  # 하나만 찾으면 중단

    # 8. 임시 폴더 통계
    print("\n8. 임시 폴더 상태")
    print("-" * 50)
    stats = processor.get_temp_stats()
    print(f"   - 기본 디렉토리: {stats['base_directory']}")
    print(f"   - 메일 폴더 수: {stats['total_folders']}개")
    print(f"   - 전체 크기: {stats['total_size']:,} bytes")

    for folder in stats['mail_folders'][:3]:  # 최대 3개만
        print(f"     • {folder['name']}: {folder['files']}개 파일, {folder['size']:,} bytes")

    # 9. 정리
    print("\n9. 정리")
    print("-" * 50)
    cleanup = input("임시 파일을 정리하시겠습니까? (y/n): ")
    if cleanup.lower() == 'y':
        processor.cleanup_all_temp()
        print("✅ 임시 파일 정리 완료")
    else:
        print(f"ℹ️ 임시 파일 유지: {processor.temp_base}")

    # 종료
    await auth_manager.close()
    print("\n" + "=" * 70)
    print("테스트 완료!")


async def test_simple():
    """간단한 테스트 (인증 없이)"""
    print("\n간단한 기능 테스트")
    print("=" * 50)

    # 더미 데이터로 검색 테스트
    dummy_data = [
        {
            "mail_id": "test1",
            "subject": "회의 자료",
            "search_index": "오늘 회의에서 논의할 계약 내용입니다.",
            "mail": {"body_text": "회의 자료를 첨부합니다."},
            "attachments": [
                {"name": "계약서.pdf", "text": "계약 조건은 다음과 같습니다..."}
            ]
        },
        {
            "mail_id": "test2",
            "subject": "프로젝트 진행 상황",
            "search_index": "프로젝트 일정과 예산 검토",
            "mail": {"body_text": "프로젝트 진행 상황 공유"},
            "attachments": []
        }
    ]

    # 임시 processor (토큰 없이)
    processor = MailTextProcessor(access_token="dummy_token")

    # 검색 테스트
    keywords = ["계약", "회의", "프로젝트"]

    for keyword in keywords:
        results = await processor.search_in_processed_mails(keyword, dummy_data)
        print(f"\n'{keyword}' 검색 결과:")
        for r in results:
            print(f"  - {r['subject']}: {len(r['matches'])}개 매치")

    print("\n✅ 간단한 테스트 완료")


async def main():
    """메인 함수"""
    print("\nMail-Attachment Integration Test")
    print("테스트 옵션:")
    print("1. 전체 테스트 (인증 필요)")
    print("2. 간단한 테스트 (인증 불필요)")

    choice = input("\n선택 (1 or 2): ")

    if choice == "1":
        await test_integration()
    else:
        await test_simple()


if __name__ == "__main__":
    asyncio.run(main())