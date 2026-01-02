"""
Attachment Handler
메일 첨부 파일 다운로드 전용 모듈
Graph API를 통한 첨부파일 처리 (다운로드만, 텍스트 변환 없음)
"""

import os
import base64
from typing import List, Dict, Optional, Any, Union
from pathlib import Path
import aiohttp
import asyncio


class AttachmentHandler:
    """메일 첨부 파일 다운로드 핸들러"""

    def __init__(self, access_token: str):
        """
        Args:
            access_token: Microsoft Graph API 액세스 토큰
        """
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    async def list_attachments(self, message_id: str, user_id: str = "me") -> List[Dict[str, Any]]:
        """
        특정 메일의 첨부 파일 목록 조회

        Args:
            message_id: 메일 메시지 ID
            user_id: 사용자 ID (기본값: "me")

        Returns:
            첨부 파일 정보 목록
        """
        url = f"{self.base_url}/users/{user_id}/messages/{message_id}/attachments"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    attachments = data.get("value", [])

                    # 첨부 파일 정보 정리
                    result = []
                    for attachment in attachments:
                        att_info = {
                            "id": attachment.get("id"),
                            "name": attachment.get("name"),
                            "contentType": attachment.get("contentType"),
                            "size": attachment.get("size"),
                            "isInline": attachment.get("isInline", False),
                            "@odata.type": attachment.get("@odata.type"),
                        }

                        # 파일 첨부인 경우 추가 정보
                        if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
                            att_info["contentId"] = attachment.get("contentId")
                            att_info["contentLocation"] = attachment.get("contentLocation")

                        result.append(att_info)

                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to list attachments: {response.status} - {error_text}")

    async def get_attachment(self, message_id: str, attachment_id: str, user_id: str = "me") -> Dict[str, Any]:
        """
        특정 첨부 파일의 상세 정보 및 내용 조회

        Args:
            message_id: 메일 메시지 ID
            attachment_id: 첨부 파일 ID
            user_id: 사용자 ID (기본값: "me")

        Returns:
            첨부 파일 상세 정보 (내용 포함)
        """
        url = f"{self.base_url}/users/{user_id}/messages/{message_id}/attachments/{attachment_id}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get attachment: {response.status} - {error_text}")

    async def download_attachment(
        self, message_id: str, attachment_id: str, save_path: Optional[str] = None, user_id: str = "me"
    ) -> str:
        """
        첨부 파일 다운로드 및 저장

        Args:
            message_id: 메일 메시지 ID
            attachment_id: 첨부 파일 ID
            save_path: 저장 경로 (없으면 downloads 폴더에 저장)
            user_id: 사용자 ID (기본값: "me")

        Returns:
            저장된 파일 경로
        """
        # 첨부 파일 정보 가져오기
        attachment = await self.get_attachment(message_id, attachment_id, user_id)

        # 파일명 추출
        filename = attachment.get("name", f"attachment_{attachment_id}")

        # 저장 경로 설정
        if save_path:
            file_path = Path(save_path)
        else:
            # downloads 폴더 생성
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)

            # 메시지 ID 기반 하위 폴더 생성
            message_dir = downloads_dir / message_id[:8]
            message_dir.mkdir(exist_ok=True)

            file_path = message_dir / filename

        # 파일 내용 디코딩 및 저장
        if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
            content_bytes = attachment.get("contentBytes")
            if content_bytes:
                # Base64 디코딩
                file_content = base64.b64decode(content_bytes)

                # 파일 저장
                with open(file_path, "wb") as f:
                    f.write(file_content)

                print(f"Downloaded: {file_path} ({len(file_content):,} bytes)")
                return str(file_path)
            else:
                raise ValueError("No content bytes in attachment")
        else:
            raise ValueError(f"Unsupported attachment type: {attachment.get('@odata.type')}")

    async def download_all_attachments(
        self, message_id: str, save_dir: Optional[str] = None, user_id: str = "me"
    ) -> List[str]:
        """
        메일의 모든 첨부 파일 다운로드

        Args:
            message_id: 메일 메시지 ID
            save_dir: 저장 디렉토리 경로
            user_id: 사용자 ID (기본값: "me")

        Returns:
            다운로드된 파일 경로 목록
        """
        # 첨부 파일 목록 조회
        attachments = await self.list_attachments(message_id, user_id)

        if not attachments:
            print(f"No attachments found for message {message_id}")
            return []

        print(f"Found {len(attachments)} attachment(s)")

        # 저장 디렉토리 설정
        if save_dir:
            base_dir = Path(save_dir)
        else:
            base_dir = Path("downloads") / message_id[:8]

        base_dir.mkdir(parents=True, exist_ok=True)

        # 모든 첨부 파일 다운로드
        downloaded_files = []
        for i, att in enumerate(attachments, 1):
            print(f"\n[{i}/{len(attachments)}] Downloading: {att['name']} ({att['size']:,} bytes)")

            try:
                file_path = await self.download_attachment(message_id, att["id"], str(base_dir / att["name"]), user_id)
                downloaded_files.append(file_path)
            except Exception as e:
                print(f"Failed to download {att['name']}: {e}")

        return downloaded_files

    async def process_mail_attachments(
        self,
        mail_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        download: bool = True,
        save_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        메일 조회 결과에서 첨부 파일 처리

        Args:
            mail_data: 메일 조회 결과 (단일 메일 또는 메일 목록)
            download: 첨부 파일 다운로드 여부
            save_dir: 다운로드 저장 디렉토리

        Returns:
            처리 결과 요약
        """
        results = {"processed_mails": 0, "total_attachments": 0, "downloaded_files": [], "errors": []}

        # 메일 목록으로 정규화
        if isinstance(mail_data, dict):
            if "value" in mail_data:  # Graph API response format
                mails = mail_data["value"]
            else:  # Single mail
                mails = [mail_data]
        else:
            mails = mail_data

        # 각 메일 처리
        for mail in mails:
            mail_id = mail.get("id")
            subject = mail.get("subject", "No Subject")
            has_attachments = mail.get("hasAttachments", False)

            if not mail_id:
                continue

            results["processed_mails"] += 1

            if has_attachments:
                print(f"\n📧 Processing mail: {subject}")
                print(f"   ID: {mail_id}")

                try:
                    # 첨부 파일 목록 조회
                    attachments = await self.list_attachments(mail_id)
                    results["total_attachments"] += len(attachments)

                    if attachments:
                        print(f"   Found {len(attachments)} attachment(s):")
                        for att in attachments:
                            print(f"     - {att['name']} ({att['size']:,} bytes, {att['contentType']})")

                        # 다운로드 옵션이 활성화된 경우
                        if download:
                            mail_save_dir = None
                            if save_dir:
                                mail_save_dir = Path(save_dir) / mail_id[:8]

                            downloaded = await self.download_all_attachments(
                                mail_id, str(mail_save_dir) if mail_save_dir else None
                            )
                            results["downloaded_files"].extend(downloaded)

                except Exception as e:
                    error_msg = f"Error processing mail {mail_id}: {e}"
                    print(f"   ❌ {error_msg}")
                    results["errors"].append(error_msg)

        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 Processing Summary:")
        print(f"   - Processed mails: {results['processed_mails']}")
        print(f"   - Total attachments: {results['total_attachments']}")
        print(f"   - Downloaded files: {len(results['downloaded_files'])}")
        if results["errors"]:
            print(f"   - Errors: {len(results['errors'])}")

        return results


async def main():
    """테스트용 메인 함수"""
    # 환경 변수에서 토큰 읽기
    access_token = os.getenv("GRAPH_ACCESS_TOKEN")
    if not access_token:
        print("Please set GRAPH_ACCESS_TOKEN environment variable")
        return

    handler = AttachmentHandler(access_token)

    # 테스트할 메일 ID (실제 메일 ID로 교체 필요)
    test_message_id = "YOUR_MESSAGE_ID_HERE"

    try:
        # 첨부 파일 목록 조회
        attachments = await handler.list_attachments(test_message_id)
        print(f"Found {len(attachments)} attachments")

        # 모든 첨부 파일 다운로드
        if attachments:
            downloaded = await handler.download_all_attachments(test_message_id)
            print(f"Downloaded {len(downloaded)} files")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
