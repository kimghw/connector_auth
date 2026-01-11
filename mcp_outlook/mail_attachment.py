"""
Graph Attachment Handler - 메일 첨부파일 Processor
$batch + $expand=attachments로 조회된 메일의 첨부파일을 처리

역할:
    - 첨부파일 다운로드 및 저장
    - 폴더 구조 관리
    - 메타데이터 관리 및 중복 제거

Classes:
    - MailMetadataManager: 메타정보 저장 및 중복 제거
    - BatchAttachmentHandler: 배치 첨부파일 처리
    - SingleAttachmentHandler: 개별 첨부파일 처리

Note:
    MailFolderManager는 mail_attachment_storage.py로 이동됨
    (LocalStorageBackend의 alias로 하위 호환성 유지)
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
from typing import TYPE_CHECKING

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if TYPE_CHECKING:
    from core.protocols import TokenProviderProtocol
from .graph_mail_url import ExpandBuilder, GraphMailUrlBuilder
from .mail_attachment_storage import StorageBackend, LocalStorageBackend, OneDriveStorageBackend, get_storage_backend, MailFolderManager
from .mail_attachment_converter import ConversionPipeline, get_conversion_pipeline
from .mail_attachment_processor import (
    process_body_content,
    process_attachments,
    process_attachment_with_conversion,
    process_attachment_original,
)


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


class BatchAttachmentHandler:
    """
    배치 첨부파일 핸들러
    $batch + $expand=attachments로 메일과 첨부파일을 한번에 조회 및 저장
    """

    def __init__(
        self,
        base_directory: str = "downloads",
        metadata_file: str = "mail_metadata.json",
        token_provider: Optional["TokenProviderProtocol"] = None,
    ):
        """
        초기화

        Args:
            base_directory: 첨부파일 저장 기본 디렉토리
            metadata_file: 메타데이터 파일명 (base_directory 안에 저장됨)
            token_provider: 토큰 제공자 (None이면 기본 AuthManager 사용)
        """
        if token_provider is None:
            from session.auth_manager import AuthManager
            token_provider = AuthManager()
        self.token_provider = token_provider
        self.folder_manager = MailFolderManager(base_directory)
        # metadata_file을 base_directory 안에 저장
        metadata_path = str(Path(base_directory) / metadata_file)
        self.metadata_manager = MailMetadataManager(metadata_path)
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
            return await self.token_provider.validate_and_refresh_token(user_email)
        except Exception as e:
            print(f"토큰 획득 실패: {e}")
            return None

    def _build_batch_requests(
        self,
        user_email: str,
        message_ids: List[str],
        select_params: Optional[Any] = None,  # SelectParams 또는 List[str]
    ) -> List[Dict[str, Any]]:
        """
        $batch 요청 본문 생성

        Args:
            user_email: 사용자 이메일
            message_ids: 메일 ID 목록
            select_params: SelectParams 객체 또는 필드 목록

        Returns:
            $batch requests 배열
        """
        from .outlook_types import SelectParams, build_select_query

        # ExpandBuilder 설정
        self.expand_builder.reset()

        # select_params 처리
        select_fields = None
        if select_params:
            if isinstance(select_params, SelectParams):
                # SelectParams 객체인 경우 build_select_query 사용
                select_query = build_select_query(select_params)
                select_fields = select_query.split(",") if select_query else None
            elif isinstance(select_params, list):
                # 리스트인 경우 그대로 사용 (하위 호환성)
                select_fields = select_params

        # 기본 필드 (필수) + 사용자 정의 필드
        # - id: 메일 식별, 중복 체크
        # - subject: 폴더명 생성
        # - from: 폴더명 생성 (보낸사람)
        # - receivedDateTime: 폴더명 생성 (날짜)
        # - body: 메일 본문 저장
        # - hasAttachments: 첨부파일 유무 확인
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

    async def fetch_metadata_only(
        self,
        user_email: str,
        message_ids: List[str],
        select_params: Optional[Any] = None,  # SelectParams 또는 List[str]
    ) -> Dict[str, Any]:
        """
        메일과 첨부파일의 메타데이터만 조회 (다운로드 없음)

        Args:
            user_email: 사용자 이메일
            message_ids: 메일 ID 목록
            select_params: SelectParams 객체 또는 필드 목록

        Returns:
            메타데이터 조회 결과
        """
        result = {
            "success": False,
            "messages": [],
            "total_processed": 0,
            "attachments_count": 0,
            "errors": [],
        }

        if not message_ids:
            result["success"] = True
            result["message"] = "No messages to process"
            return result

        # 토큰 획득
        access_token = await self._get_access_token(user_email)
        if not access_token:
            result["errors"].append("Failed to acquire access token")
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

        print(f"\n📋 Fetching metadata for {len(message_ids)} emails ({len(batches)} batches)")

        async with aiohttp.ClientSession() as session:
            for batch_num, batch_ids in enumerate(batches, 1):
                print(f"\n=== Batch {batch_num}/{len(batches)} ({len(batch_ids)} emails) ===")

                # 배치 요청 생성
                requests = self._build_batch_requests(user_email, batch_ids, select_params)
                batch_body = {"requests": requests}

                try:
                    async with session.post(
                        self.batch_url, headers=headers, json=batch_body
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            result["errors"].append(f"Batch {batch_num} failed: {error_text[:200]}")
                            continue

                        batch_response = await response.json()

                        # 각 응답 처리 (메타데이터만)
                        for resp in batch_response.get("responses", []):
                            req_id = int(resp.get("id", 0)) - 1
                            if req_id < 0 or req_id >= len(batch_ids):
                                continue

                            message_id = batch_ids[req_id]

                            if resp.get("status") != 200:
                                error_msg = resp.get("body", {}).get("error", {}).get("message", "Unknown")
                                result["errors"].append(f"Mail {message_id[:20]}...: {error_msg}")
                                continue

                            mail_data = resp.get("body", {})

                            # 메타데이터 추출
                            metadata = {
                                "id": mail_data.get("id"),
                                "subject": mail_data.get("subject"),
                                "from": mail_data.get("from", {}).get("emailAddress", {}),
                                "toRecipients": mail_data.get("toRecipients", []),
                                "receivedDateTime": mail_data.get("receivedDateTime"),
                                "hasAttachments": mail_data.get("hasAttachments", False),
                                "importance": mail_data.get("importance"),
                                "isRead": mail_data.get("isRead"),
                                "bodyPreview": mail_data.get("bodyPreview", ""),
                                "body": mail_data.get("body", {}),  # 전체 본문 포함
                                "attachments": []
                            }

                            # 첨부파일 메타데이터 추출
                            attachments = mail_data.get("attachments", [])
                            for att in attachments:
                                att_meta = {
                                    "id": att.get("id"),
                                    "name": att.get("name"),
                                    "contentType": att.get("contentType"),
                                    "size": att.get("size", 0),
                                    "isInline": att.get("isInline", False),
                                    "@odata.type": att.get("@odata.type"),
                                }
                                metadata["attachments"].append(att_meta)
                                result["attachments_count"] += 1

                            result["messages"].append(metadata)
                            result["total_processed"] += 1

                            print(f"✅ {metadata['subject'][:50]}... ({len(attachments)} attachments)")

                except Exception as e:
                    result["errors"].append(f"Batch {batch_num} exception: {str(e)}")

        result["success"] = result["total_processed"] > 0
        result["message"] = f"Fetched metadata for {result['total_processed']} emails"

        return result

    async def fetch_and_save(
        self,
        user_email: str,
        message_ids: List[str],
        select_params: Optional[Any] = None,  # SelectParams 또는 List[str]
        skip_duplicates: bool = True,
        save_file: bool = True,
        storage_type: str = "local",
        convert_to_txt: bool = False,
        include_body: bool = True,
        onedrive_folder: str = "/Attachments",
    ) -> Dict[str, Any]:
        """
        메일과 첨부파일을 조회하여 저장

        Args:
            user_email: 사용자 이메일
            message_ids: 메일 ID 목록
            select_params: SelectParams 객체 또는 필드 목록
            skip_duplicates: 중복 메일 건너뛰기
            save_file: 파일 저장 여부 (False면 메모리 반환만)
            storage_type: 저장 위치 ("local" 또는 "onedrive")
            convert_to_txt: 첨부파일을 TXT로 변환 여부
            include_body: 본문 포함 여부 (False면 첨부파일만)
            onedrive_folder: OneDrive 저장 폴더 경로

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
            "converted_files": [],
            "body_contents": [],          # save_file=False일 때 본문 내용
            "attachment_contents": [],    # save_file=False일 때 첨부파일 내용
            "errors": [],
            "storage_type": storage_type,
            "save_file": save_file,
            "convert_to_txt": convert_to_txt,
            "include_body": include_body,
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

        # Storage Backend 생성 (저장 모드일 때만)
        storage = None
        if save_file:
            storage = get_storage_backend(
                storage_type=storage_type,
                auth_manager=self.auth_manager,
                user_email=user_email,
                base_directory=str(self.folder_manager.base_directory),
                base_folder=onedrive_folder,
            )

        # Converter 생성 (필요시)
        converter = get_conversion_pipeline() if convert_to_txt else None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # 배치 분할
        batches = [
            message_ids[i : i + self.max_batch_size]
            for i in range(0, len(message_ids), self.max_batch_size)
        ]

        storage_label = "메모리 반환" if not save_file else ("OneDrive" if storage_type == "onedrive" else "Local")
        convert_label = " + TXT변환" if convert_to_txt else ""
        body_label = " + 본문" if include_body else ""
        print(f"\n처리할 메일: {len(message_ids)}개 ({len(batches)} 배치) [{storage_label}{convert_label}{body_label}]")

        async with aiohttp.ClientSession() as session:
            for batch_num, batch_ids in enumerate(batches, 1):
                print(f"\n=== 배치 {batch_num}/{len(batches)} ({len(batch_ids)}개) ===")

                # 배치 요청 생성
                requests = self._build_batch_requests(user_email, batch_ids, select_params)
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
                            await self._process_mail_with_options(
                                mail_data, result, storage, converter,
                                save_file=save_file, include_body=include_body
                            )

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

    async def _process_mail_with_options(
        self,
        mail_data: Dict[str, Any],
        result: Dict[str, Any],
        storage: Optional[StorageBackend],
        converter: Optional[ConversionPipeline] = None,
        save_file: bool = True,
        include_body: bool = True
    ):
        """
        단일 메일 처리 오케스트레이터 (Storage Backend 및 Converter 옵션 적용)

        본문 처리와 첨부파일 처리를 mail_attachment_processor 모듈에 위임

        Args:
            mail_data: 메일 데이터
            result: 결과 딕셔너리 (업데이트됨)
            storage: 저장소 백엔드 (Local 또는 OneDrive), save_file=False면 None
            converter: 텍스트 변환기 (None이면 원본 저장)
            save_file: 파일 저장 여부 (False면 메모리 반환만)
            include_body: 본문 포함 여부
        """
        message_id = mail_data.get("id", "")
        subject = mail_data.get("subject", "제목 없음")

        mode_label = "저장" if save_file else "반환"
        print(f"\n[{mode_label}] {subject[:50]}...")

        try:
            folder_path = None
            saved_files = []

            # Step 1: 저장 모드일 때만 폴더 생성
            if save_file and storage:
                folder_path = await storage.create_folder(mail_data)

            # Step 2: 메일 본문 처리 (processor 모듈 호출)
            if include_body:
                body_saved = await process_body_content(
                    mail_data, result, storage, folder_path, save_file
                )
                if body_saved:
                    saved_files.append(body_saved)

            # Step 3: 첨부파일 처리 (processor 모듈 호출)
            attachment_saved = await process_attachments(
                mail_data, result, storage, converter, folder_path, save_file
            )
            saved_files.extend(attachment_saved)

            # Step 4: 메타데이터 저장 (저장 모드일 때만)
            if save_file:
                self.metadata_manager.add_processed_mail(
                    message_id, mail_data, str(folder_path) if folder_path else "", saved_files
                )

            result["processed"] += 1

        except Exception as e:
            result["errors"].append(f"메일 처리 실패 ({subject[:30]}...): {str(e)}")

    async def fetch_specific_attachments(
        self,
        user_email: str,
        attachments_info: List[Dict[str, str]],
        save_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        특정 첨부파일들을 선택적으로 다운로드 (메일 ID와 첨부파일 ID 지정)

        Args:
            user_email: 사용자 이메일
            attachments_info: [{"message_id": "...", "attachment_id": "..."}, ...]
            save_directory: 저장 디렉토리

        Returns:
            처리 결과
        """
        result = {
            "success": False,
            "total_requested": len(attachments_info),
            "downloaded": 0,
            "failed": 0,
            "results": [],
            "errors": [],
        }

        if not attachments_info:
            result["success"] = True
            result["message"] = "No attachments to process"
            return result

        # 토큰 획득
        access_token = await self._get_access_token(user_email)
        if not access_token:
            result["errors"].append("Failed to acquire access token")
            return result

        handler = SingleAttachmentHandler(access_token)

        for info in attachments_info:
            message_id = info.get("message_id")
            attachment_id = info.get("attachment_id")

            if not message_id or not attachment_id:
                result["errors"].append(f"Invalid attachment info: {info}")
                result["failed"] += 1
                continue

            try:
                # 첨부파일 다운로드
                attachment_data = await handler.get_attachment(message_id, attachment_id, user_email)

                # 파일명 및 경로 설정
                file_name = attachment_data.get("name", f"attachment_{attachment_id}")

                if save_directory:
                    folder_path = Path(save_directory) / message_id[:8]
                else:
                    folder_path = Path(self.folder_manager.base_directory) / message_id[:8]

                folder_path.mkdir(parents=True, exist_ok=True)
                file_path = str(folder_path / file_name)

                # 저장
                saved_path = await handler.download_attachment(
                    message_id, attachment_id, file_path, user_email
                )

                result["results"].append({
                    "message_id": message_id,
                    "attachment_id": attachment_id,
                    "file_path": saved_path,
                    "name": file_name,
                    "success": True,
                })
                result["downloaded"] += 1

            except Exception as e:
                result["errors"].append(f"Failed {message_id}/{attachment_id}: {str(e)}")
                result["results"].append({
                    "message_id": message_id,
                    "attachment_id": attachment_id,
                    "success": False,
                    "error": str(e),
                })
                result["failed"] += 1

        result["success"] = result["downloaded"] > 0
        result["message"] = f"Downloaded {result['downloaded']}/{result['total_requested']} attachments"

        return result

    async def close(self):
        """리소스 정리"""
        await self.auth_manager.close()

class SingleAttachmentHandler:
    """
    개별 첨부파일 조회/다운로드용 핸들러

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
