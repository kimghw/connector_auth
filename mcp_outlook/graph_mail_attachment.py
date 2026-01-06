"""
Graph Attachment Handler - 메일 첨부파일 Processor
$batch + $expand=attachments로 조회된 메일의 첨부파일을 처리

역할:
    - 첨부파일 다운로드 및 저장
    - 폴더 구조 관리
    - 메타데이터 관리 및 중복 제거

Classes:
    - MailFolderManager: 폴더 생성 및 파일 저장
    - MailMetadataManager: 메타정보 저장 및 중복 제거
    - GraphAttachmentHandler: 배치 첨부파일 처리
    - AttachmentHandler: 개별 첨부파일 처리
"""

import os
import re
import json
import base64
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from session.auth_manager import AuthManager
from .graph_mail_url import ExpandBuilder, GraphMailUrlBuilder


class MailFolderManager:
    """
    메일 폴더 및 파일 관리
    메일별로 폴더를 생성하고 첨부파일/메일 본문을 저장

    폴더명 형식: {날짜}_{보낸사람}_{제목}
    """

    # 파일시스템에서 사용 불가한 특수문자
    INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

    def __init__(self, base_directory: str = "downloads"):
        """
        초기화

        Args:
            base_directory: 기본 저장 디렉토리
        """
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, name: str, max_length: int = 50) -> str:
        """
        파일명에서 특수문자 제거

        Args:
            name: 원본 파일명
            max_length: 최대 길이

        Returns:
            정제된 파일명
        """
        # 특수문자 제거
        sanitized = re.sub(self.INVALID_CHARS, "", name)
        # 공백 정리
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        # 길이 제한
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        # 빈 문자열 방지
        if not sanitized:
            sanitized = "untitled"
        return sanitized

    def create_folder_name(self, mail_data: Dict[str, Any]) -> str:
        """
        메일 데이터로부터 폴더명 생성

        Args:
            mail_data: 메일 데이터 (subject, from, receivedDateTime 필요)

        Returns:
            폴더명 (형식: YYYYMMDD_보낸사람_제목)
        """
        # 날짜 추출
        received_dt = mail_data.get("receivedDateTime", "")
        if received_dt:
            try:
                dt = datetime.fromisoformat(received_dt.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y%m%d")
            except (ValueError, AttributeError):
                date_str = datetime.now().strftime("%Y%m%d")
        else:
            date_str = datetime.now().strftime("%Y%m%d")

        # 보낸 사람 추출
        from_info = mail_data.get("from", {})
        email_addr = from_info.get("emailAddress", {})
        sender = email_addr.get("name") or email_addr.get("address", "unknown")
        sender = self.sanitize_filename(sender, max_length=30)

        # 제목 추출
        subject = mail_data.get("subject", "no_subject")
        subject = self.sanitize_filename(subject, max_length=50)

        return f"{date_str}_{sender}_{subject}"

    def get_mail_folder_path(self, mail_data: Dict[str, Any]) -> Path:
        """
        메일에 해당하는 폴더 경로 반환 (필요시 생성)

        Args:
            mail_data: 메일 데이터

        Returns:
            폴더 경로
        """
        folder_name = self.create_folder_name(mail_data)
        folder_path = self.base_directory / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def save_attachment(
        self, folder_path: Path, attachment: Dict[str, Any]
    ) -> Optional[str]:
        """
        첨부파일 저장

        Args:
            folder_path: 저장할 폴더 경로
            attachment: 첨부파일 데이터 (name, contentBytes 필요)

        Returns:
            저장된 파일 경로 또는 None
        """
        name = attachment.get("name", "attachment")
        content_bytes = attachment.get("contentBytes")

        if not content_bytes:
            print(f"  [SKIP] {name} - contentBytes 없음 (대용량 파일)")
            return None

        # 파일명 정제
        safe_name = self.sanitize_filename(name, max_length=100)

        # 중복 파일명 처리
        file_path = folder_path / safe_name
        counter = 1
        while file_path.exists():
            name_parts = safe_name.rsplit(".", 1)
            if len(name_parts) == 2:
                new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                new_name = f"{safe_name}_{counter}"
            file_path = folder_path / new_name
            counter += 1

        try:
            # Base64 디코딩 및 저장
            file_content = base64.b64decode(content_bytes)
            with open(file_path, "wb") as f:
                f.write(file_content)

            print(f"  [SAVED] {file_path.name} ({len(file_content):,} bytes)")
            return str(file_path)

        except Exception as e:
            print(f"  [ERROR] {name} 저장 실패: {e}")
            return None

    def save_mail_content(
        self, folder_path: Path, mail_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        메일 본문을 txt 파일로 저장

        Args:
            folder_path: 저장할 폴더 경로
            mail_data: 메일 데이터

        Returns:
            저장된 파일 경로 또는 None
        """
        try:
            file_path = folder_path / "mail_content.txt"

            # 메일 정보 구성
            content_lines = [
                "=" * 60,
                f"Subject: {mail_data.get('subject', 'N/A')}",
                f"From: {mail_data.get('from', {}).get('emailAddress', {}).get('address', 'N/A')}",
                f"Received: {mail_data.get('receivedDateTime', 'N/A')}",
                f"Message ID: {mail_data.get('id', 'N/A')}",
                "=" * 60,
                "",
            ]

            # 본문 추출
            body = mail_data.get("body", {})
            body_content = body.get("content", "")
            body_type = body.get("contentType", "text")

            if body_type == "html":
                # HTML 태그 간단히 제거
                import re

                body_content = re.sub(r"<[^>]+>", "", body_content)
                body_content = re.sub(r"&nbsp;", " ", body_content)
                body_content = re.sub(r"&lt;", "<", body_content)
                body_content = re.sub(r"&gt;", ">", body_content)
                body_content = re.sub(r"&amp;", "&", body_content)

            content_lines.append(body_content)

            # 파일 저장
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content_lines))

            print(f"  [SAVED] mail_content.txt")
            return str(file_path)

        except Exception as e:
            print(f"  [ERROR] 메일 본문 저장 실패: {e}")
            return None


class MailMetadataManager:
    """
    메일 메타데이터 관리
    message_id 기반 중복 제거 및 처리 이력 관리
    """

    def __init__(self, metadata_file: str = "mail_metadata.json"):
        """
        초기화

        Args:
            metadata_file: 메타데이터 파일 경로
        """
        self.metadata_file = Path(metadata_file)
        self._metadata: Dict[str, Any] = {}
        self._load_metadata()

    def _load_metadata(self):
        """메타데이터 파일 로드"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"메타데이터 로드 실패: {e}")
                self._metadata = {}
        else:
            self._metadata = {"processed_messages": {}, "last_updated": None}

    def _save_metadata(self):
        """메타데이터 파일 저장"""
        try:
            self._metadata["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"메타데이터 저장 실패: {e}")

    def is_duplicate(self, message_id: str) -> bool:
        """
        중복 메일 여부 확인

        Args:
            message_id: 메일 ID

        Returns:
            True if 이미 처리된 메일
        """
        return message_id in self._metadata.get("processed_messages", {})

    def add_processed_mail(
        self,
        message_id: str,
        mail_data: Dict[str, Any],
        folder_path: str,
        saved_files: List[str],
    ):
        """
        처리된 메일 정보 추가

        Args:
            message_id: 메일 ID
            mail_data: 메일 데이터
            folder_path: 저장된 폴더 경로
            saved_files: 저장된 파일 목록
        """
        if "processed_messages" not in self._metadata:
            self._metadata["processed_messages"] = {}

        self._metadata["processed_messages"][message_id] = {
            "subject": mail_data.get("subject", ""),
            "from": mail_data.get("from", {}).get("emailAddress", {}).get("address", ""),
            "received_datetime": mail_data.get("receivedDateTime", ""),
            "folder_path": folder_path,
            "saved_files": saved_files,
            "processed_at": datetime.now().isoformat(),
            "attachment_count": len(mail_data.get("attachments", [])),
        }

        self._save_metadata()

    def get_processed_count(self) -> int:
        """처리된 메일 수 반환"""
        return len(self._metadata.get("processed_messages", {}))

    def get_processed_message_ids(self) -> List[str]:
        """처리된 메일 ID 목록 반환"""
        return list(self._metadata.get("processed_messages", {}).keys())

    def filter_new_messages(self, message_ids: List[str]) -> List[str]:
        """
        새로운 메일 ID만 필터링

        Args:
            message_ids: 전체 메일 ID 목록

        Returns:
            아직 처리되지 않은 메일 ID 목록
        """
        return [mid for mid in message_ids if not self.is_duplicate(mid)]


class GraphAttachmentHandler:
    """
    Graph API 첨부파일 핸들러
    $batch + $expand=attachments로 메일과 첨부파일을 한번에 조회 및 저장
    """

    def __init__(
        self,
        base_directory: str = "downloads",
        metadata_file: str = "mail_metadata.json",
    ):
        """
        초기화

        Args:
            base_directory: 첨부파일 저장 기본 디렉토리
            metadata_file: 메타데이터 파일 경로
        """
        self.auth_manager = AuthManager()
        self.folder_manager = MailFolderManager(base_directory)
        self.metadata_manager = MailMetadataManager(metadata_file)
        self.expand_builder = ExpandBuilder()

        self.batch_url = "https://graph.microsoft.com/v1.0/$batch"
        self.max_batch_size = 20

    async def _get_access_token(self, user_email: str) -> Optional[str]:
        """
        액세스 토큰 획득

        Args:
            user_email: 사용자 이메일

        Returns:
            액세스 토큰 또는 None
        """
        try:
            return await self.auth_manager.validate_and_refresh_token(user_email)
        except Exception as e:
            print(f"토큰 획득 실패: {e}")
            return None

    def _build_batch_requests(
        self,
        user_email: str,
        message_ids: List[str],
        select_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        $batch 요청 본문 생성

        Args:
            user_email: 사용자 이메일
            message_ids: 메일 ID 목록
            select_fields: 선택할 필드 목록

        Returns:
            $batch requests 배열
        """
        # ExpandBuilder 설정
        self.expand_builder.reset()

        # 기본 필드 + 사용자 정의 필드
        default_fields = ["id", "subject", "from", "receivedDateTime", "body", "hasAttachments"]
        if select_fields:
            all_fields = list(set(default_fields + select_fields))
        else:
            all_fields = default_fields

        self.expand_builder.select(all_fields).expand_attachments()

        requests = []
        for i, message_id in enumerate(message_ids):
            url = self.expand_builder.build_url(f"/users/{user_email}/messages/{message_id}")
            requests.append({"id": str(i + 1), "method": "GET", "url": url})

        return requests

    async def fetch_and_save(
        self,
        user_email: str,
        message_ids: List[str],
        select_fields: Optional[List[str]] = None,
        skip_duplicates: bool = True,
    ) -> Dict[str, Any]:
        """
        메일과 첨부파일을 조회하여 저장

        Args:
            user_email: 사용자 이메일
            message_ids: 메일 ID 목록
            select_fields: 추가 선택 필드
            skip_duplicates: 중복 메일 건너뛰기

        Returns:
            처리 결과
        """
        result = {
            "success": False,
            "total_requested": len(message_ids),
            "processed": 0,
            "skipped_duplicates": 0,
            "saved_mails": [],
            "saved_attachments": [],
            "errors": [],
        }

        if not message_ids:
            result["success"] = True
            result["message"] = "처리할 메일 없음"
            return result

        # 중복 필터링
        if skip_duplicates:
            new_message_ids = self.metadata_manager.filter_new_messages(message_ids)
            result["skipped_duplicates"] = len(message_ids) - len(new_message_ids)
            message_ids = new_message_ids

            if not message_ids:
                result["success"] = True
                result["message"] = "모든 메일이 이미 처리됨"
                return result

        # 토큰 획득
        access_token = await self._get_access_token(user_email)
        if not access_token:
            result["errors"].append("토큰 획득 실패")
            return result

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # 배치 분할
        batches = [
            message_ids[i : i + self.max_batch_size]
            for i in range(0, len(message_ids), self.max_batch_size)
        ]

        print(f"\n처리할 메일: {len(message_ids)}개 ({len(batches)} 배치)")

        async with aiohttp.ClientSession() as session:
            for batch_num, batch_ids in enumerate(batches, 1):
                print(f"\n=== 배치 {batch_num}/{len(batches)} ({len(batch_ids)}개) ===")

                # 배치 요청 생성
                requests = self._build_batch_requests(user_email, batch_ids, select_fields)
                batch_body = {"requests": requests}

                try:
                    async with session.post(
                        self.batch_url, headers=headers, json=batch_body
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            result["errors"].append(f"배치 {batch_num} 실패: {error_text[:200]}")
                            continue

                        batch_response = await response.json()

                        # 각 응답 처리
                        for resp in batch_response.get("responses", []):
                            req_id = int(resp.get("id", 0)) - 1
                            if req_id < 0 or req_id >= len(batch_ids):
                                continue

                            message_id = batch_ids[req_id]

                            if resp.get("status") != 200:
                                error_msg = resp.get("body", {}).get("error", {}).get("message", "Unknown")
                                result["errors"].append(f"메일 {message_id[:20]}...: {error_msg}")
                                continue

                            mail_data = resp.get("body", {})
                            await self._process_mail(mail_data, result)

                except Exception as e:
                    result["errors"].append(f"배치 {batch_num} 예외: {str(e)}")

        result["success"] = result["processed"] > 0
        result["message"] = f"{result['processed']}개 메일 처리 완료"

        return result

    async def _process_mail(self, mail_data: Dict[str, Any], result: Dict[str, Any]):
        """
        단일 메일 처리 (폴더 생성, 첨부파일/본문 저장)

        Args:
            mail_data: 메일 데이터
            result: 결과 딕셔너리 (업데이트됨)
        """
        message_id = mail_data.get("id", "")
        subject = mail_data.get("subject", "제목 없음")

        print(f"\n[처리] {subject[:50]}...")

        try:
            # 폴더 생성
            folder_path = self.folder_manager.get_mail_folder_path(mail_data)

            saved_files = []

            # 메일 본문 저장
            mail_file = self.folder_manager.save_mail_content(folder_path, mail_data)
            if mail_file:
                saved_files.append(mail_file)
                result["saved_mails"].append(mail_file)

            # 첨부파일 저장
            attachments = mail_data.get("attachments", [])
            for attachment in attachments:
                att_file = self.folder_manager.save_attachment(folder_path, attachment)
                if att_file:
                    saved_files.append(att_file)
                    result["saved_attachments"].append(att_file)

            # 메타데이터 저장
            self.metadata_manager.add_processed_mail(
                message_id, mail_data, str(folder_path), saved_files
            )

            result["processed"] += 1

        except Exception as e:
            result["errors"].append(f"메일 처리 실패 ({subject[:30]}...): {str(e)}")

    async def close(self):
        """리소스 정리"""
        await self.auth_manager.close()


class AttachmentHandler:
    """
    개별 첨부파일 조회/다운로드용 어댑터 클래스

    메서드:
        - list_attachments(message_id, user_id="me")
        - get_attachment(message_id, attachment_id, user_id="me")
        - download_attachment(message_id, attachment_id, save_path, user_id="me")
    """

    def __init__(self, access_token: str):
        """
        초기화

        Args:
            access_token: Microsoft Graph API 액세스 토큰
        """
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def list_attachments(
        self, message_id: str, user_id: str = "me"
    ) -> List[Dict[str, Any]]:
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

                        if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
                            att_info["contentId"] = attachment.get("contentId")
                            att_info["contentLocation"] = attachment.get("contentLocation")

                        result.append(att_info)

                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to list attachments: {response.status} - {error_text}")

    async def get_attachment(
        self, message_id: str, attachment_id: str, user_id: str = "me"
    ) -> Dict[str, Any]:
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
        self,
        message_id: str,
        attachment_id: str,
        save_path: Optional[str] = None,
        user_id: str = "me",
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
        attachment = await self.get_attachment(message_id, attachment_id, user_id)

        filename = attachment.get("name", f"attachment_{attachment_id}")

        if save_path:
            file_path = Path(save_path)
        else:
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)
            message_dir = downloads_dir / message_id[:8]
            message_dir.mkdir(exist_ok=True)
            file_path = message_dir / filename

        if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
            content_bytes = attachment.get("contentBytes")
            if content_bytes:
                file_content = base64.b64decode(content_bytes)

                # 디렉토리 생성
                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, "wb") as f:
                    f.write(file_content)

                return str(file_path)
            else:
                raise ValueError("No content bytes in attachment")
        else:
            raise ValueError(f"Unsupported attachment type: {attachment.get('@odata.type')}")
