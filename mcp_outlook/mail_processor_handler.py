"""
Mail Processor Handler - 메일 처리 인터페이스
메일 쿼리 결과를 처리 옵션에 따라 적절한 프로세서로 라우팅
실제 처리는 mail_text_processor에서 수행
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

from .mail_text_processor import MailTextProcessor


class MailStorageOption(str, Enum):
    """메일 저장 옵션"""

    MEMORY = "memory"  # 메모리에만 보관 (기본값)
    TEXT_FILE = "text"  # 텍스트 파일로 저장
    JSON_FILE = "json"  # JSON 파일로 저장
    DATABASE = "database"  # 데이터베이스에 저장


class AttachmentOption(str, Enum):
    """첨부파일 처리 옵션"""

    SKIP = "skip"  # 첨부파일 무시
    DOWNLOAD_ONLY = "download"  # 다운로드만
    DOWNLOAD_CONVERT = "convert"  # 다운로드 + 텍스트 변환
    CONVERT_DELETE = "convert_delete"  # 변환 후 원본 삭제


class OutputFormat(str, Enum):
    """출력 형식"""

    COMBINED = "combined"  # 통합 형식
    SEPARATED = "separated"  # 분리 형식
    STRUCTURED = "structured"  # 구조화 형식


class ProcessingOptions:
    """메일 처리 옵션"""

    def __init__(
        self,
        mail_storage: MailStorageOption = MailStorageOption.MEMORY,
        attachment_handling: AttachmentOption = AttachmentOption.SKIP,
        output_format: OutputFormat = OutputFormat.COMBINED,
        save_directory: Optional[str] = None,
        keep_structure: bool = True,
        cleanup_after: bool = False,
        include_metadata: bool = True,
        db_config: Optional[Dict] = None,
    ):
        self.mail_storage = mail_storage
        self.attachment_handling = attachment_handling
        self.output_format = output_format
        self.save_directory = Path(save_directory) if save_directory else Path("mail_data")
        self.keep_structure = keep_structure
        self.cleanup_after = cleanup_after
        self.include_metadata = include_metadata
        self.db_config = db_config or {}


class StorageInterface(ABC):
    """저장소 인터페이스"""

    @abstractmethod
    async def save_mail(self, mail_data: Dict[str, Any]) -> bool:
        """메일 데이터 저장"""
        pass

    @abstractmethod
    async def save_attachment(self, attachment_data: Dict[str, Any]) -> bool:
        """첨부파일 데이터 저장"""
        pass

    @abstractmethod
    async def get_mail(self, mail_id: str) -> Optional[Dict[str, Any]]:
        """메일 데이터 조회"""
        pass

    @abstractmethod
    async def close(self):
        """연결 종료"""
        pass


class MemoryStorage(StorageInterface):
    """메모리 저장소"""

    def __init__(self):
        self.storage = {}

    async def save_mail(self, mail_data: Dict[str, Any]) -> bool:
        mail_id = mail_data.get("id") or mail_data.get("mail_id")
        self.storage[mail_id] = mail_data
        return True

    async def save_attachment(self, attachment_data: Dict[str, Any]) -> bool:
        # 메모리에는 첨부파일 참조만 저장
        return True

    async def get_mail(self, mail_id: str) -> Optional[Dict[str, Any]]:
        return self.storage.get(mail_id)

    async def close(self):
        pass


class FileStorage(StorageInterface):
    """파일 저장소"""

    def __init__(self, base_directory: Path, format_type: str = "json"):
        self.base_directory = base_directory
        self.base_directory.mkdir(parents=True, exist_ok=True)
        self.format_type = format_type

    async def save_mail(self, mail_data: Dict[str, Any]) -> bool:
        mail_id = mail_data.get("id") or mail_data.get("mail_id")
        mail_id_short = mail_id[:8] if mail_id else "unknown"

        if self.format_type == "json":
            file_path = self.base_directory / f"mail_{mail_id_short}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(mail_data, f, ensure_ascii=False, indent=2)
        else:  # text
            file_path = self.base_directory / f"mail_{mail_id_short}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self._format_as_text(mail_data))

        return True

    async def save_attachment(self, attachment_data: Dict[str, Any]) -> bool:
        # 첨부파일은 별도 디렉토리에 저장
        att_dir = self.base_directory / "attachments"
        att_dir.mkdir(exist_ok=True)
        # 실제 저장 로직은 AttachmentHandler에서 처리
        return True

    async def get_mail(self, mail_id: str) -> Optional[Dict[str, Any]]:
        mail_id_short = mail_id[:8] if mail_id else "unknown"

        if self.format_type == "json":
            file_path = self.base_directory / f"mail_{mail_id_short}.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)

        return None

    async def close(self):
        pass

    def _format_as_text(self, mail_data: Dict[str, Any]) -> str:
        """메일 데이터를 텍스트 형식으로 변환"""
        lines = []
        lines.append(f"Subject: {mail_data.get('subject', 'No Subject')}")
        lines.append(f"From: {mail_data.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')}")
        lines.append(f"Date: {mail_data.get('receivedDateTime', 'Unknown')}")
        lines.append(f"ID: {mail_data.get('id', 'Unknown')}")
        lines.append("-" * 60)
        lines.append(mail_data.get("body", {}).get("content", ""))

        if mail_data.get("attachments"):
            lines.append("\n" + "=" * 60)
            lines.append("Attachments:")
            for att in mail_data.get("attachments", []):
                lines.append(f"  - {att.get('name', 'Unknown')}")

        return "\n".join(lines)


class DatabaseStorage(StorageInterface):
    """데이터베이스 저장소 인터페이스"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        # 실제 구현은 나중에
        # self.connection = None

    async def connect(self):
        """DB 연결 - 구현 필요"""
        # Implementation would go here
        pass

    async def save_mail(self, mail_data: Dict[str, Any]) -> bool:
        """메일을 DB에 저장 - 구현 필요"""
        # INSERT INTO mails (id, subject, from_address, body, received_at, ...)
        # VALUES (?, ?, ?, ?, ?, ...)
        return True

    async def save_attachment(self, attachment_data: Dict[str, Any]) -> bool:
        """첨부파일 정보를 DB에 저장 - 구현 필요"""
        # INSERT INTO attachments (id, mail_id, name, size, content_type, ...)
        # VALUES (?, ?, ?, ?, ?, ...)
        return True

    async def get_mail(self, mail_id: str) -> Optional[Dict[str, Any]]:
        """메일을 DB에서 조회 - 구현 필요"""
        # SELECT * FROM mails WHERE id = ?
        return None

    async def close(self):
        """DB 연결 종료 - 구현 필요"""
        # if self.connection:
        #     await self.connection.close()
        pass


class MailProcessorHandler:
    """메일 처리 핸들러 - 인터페이스 및 라우팅 담당"""

    def __init__(self, user_email: str, access_token: str):
        self.user_email = user_email
        self.access_token = access_token
        self.text_processor = MailTextProcessor(user_email, access_token)
        self.storage = None
        self.options = None

    async def initialize(self):
        """초기화"""
        # text_processor는 별도 초기화 필요 없음
        return True

    def set_options(self, options: ProcessingOptions):
        """처리 옵션 설정"""
        self.options = options

        # 저장소 설정
        if options.mail_storage == MailStorageOption.MEMORY:
            self.storage = MemoryStorage()
        elif options.mail_storage in [MailStorageOption.TEXT_FILE, MailStorageOption.JSON_FILE]:
            format_type = "json" if options.mail_storage == MailStorageOption.JSON_FILE else "text"
            self.storage = FileStorage(options.save_directory, format_type)
        elif options.mail_storage == MailStorageOption.DATABASE:
            self.storage = DatabaseStorage(options.db_config)

    async def process_mail(
        self, mail_data: Union[Dict[str, Any], List[Dict[str, Any]]], options: Optional[ProcessingOptions] = None
    ) -> Dict[str, Any]:
        """
        메일 처리 인터페이스 - 옵션에 따라 적절한 처리 방식 선택

        Args:
            mail_data: GraphMailQuery에서 받은 메일 데이터
            options: 처리 옵션 (없으면 기본값 사용)

        Returns:
            처리 결과
        """
        if options:
            self.set_options(options)
        elif not self.options:
            self.set_options(ProcessingOptions())  # 기본 옵션

        # 메일 목록 정규화
        if isinstance(mail_data, dict):
            if "value" in mail_data:  # Graph API 응답
                mails = mail_data["value"]
            else:  # 단일 메일
                mails = [mail_data]
        else:
            mails = mail_data

        print(f"\n📧 처리 시작: {len(mails)}개 메일")
        print(f"   저장: {self.options.mail_storage.value}")
        print(f"   첨부: {self.options.attachment_handling.value}")
        print(f"   형식: {self.options.output_format.value}")

        # 출력 형식에 따라 적절한 text_processor 메서드 호출
        processed_results = []

        for mail in mails:
            mail_id = mail.get("id", "")

            try:
                # OutputFormat에 따른 처리 방식 선택
                if self.options.output_format == OutputFormat.COMBINED:
                    # V1: 단순 통합
                    result = await self.text_processor.process_mail_v1_simple(mail_id)
                elif self.options.output_format == OutputFormat.STRUCTURED:
                    # V2: 구조화
                    result = await self.text_processor.process_mail_v2_structured(mail_id)
                elif self.options.output_format == OutputFormat.SEPARATED:
                    # V3: 분리 저장
                    keep_files = self.options.mail_storage != MailStorageOption.MEMORY
                    result = await self.text_processor.process_mail_v3_separated(mail_id, keep_files)

                # 저장소 처리
                if self.storage:
                    await self._save_to_storage(result)

                processed_results.append(result)

            except Exception as e:
                processed_results.append({"mail_id": mail_id, "status": "error", "error": str(e)})

        # 최종 결과 구성
        final_result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "options": {
                "mail_storage": self.options.mail_storage.value,
                "attachment_handling": self.options.attachment_handling.value,
                "output_format": self.options.output_format.value,
            },
            "total_processed": len(processed_results),
            "successful": len([r for r in processed_results if r.get("status") != "error"]),
            "results": processed_results,
        }

        if self.options.cleanup_after:
            self.text_processor.cleanup_all_temp()

        return final_result

    async def _save_to_storage(self, result: Dict[str, Any]) -> bool:
        """처리 결과를 설정된 저장소에 저장"""
        if self.storage:
            return await self.storage.save_mail(result)
        return True

    async def close(self):
        """리소스 정리"""
        if self.storage:
            await self.storage.close()
        # text_processor의 close는 mail_query.close()를 호출하므로 필요시 사용


# 편의 함수
async def process_fetched_mails(
    mail_data: Dict[str, Any],
    access_token: str,
    mail_storage: MailStorageOption = MailStorageOption.MEMORY,
    attachment_handling: AttachmentOption = AttachmentOption.SKIP,
    output_format: OutputFormat = OutputFormat.COMBINED,
    save_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    GraphMailQuery에서 받은 메일을 처리하는 편의 함수

    Example:
        # GraphMailQuery로 메일 조회
        query = GraphMailQuery(access_token=token)
        mail_data = await query.query_quick(unread=True, top=10)

        # 처리 옵션과 함께 처리
        result = await process_fetched_mails(
            mail_data,
            access_token=token,
            mail_storage=MailStorageOption.JSON_FILE,
            attachment_handling=AttachmentOption.DOWNLOAD_CONVERT,
            output_format=OutputFormat.STRUCTURED,
            save_directory="./processed_mails"
        )
    """
    handler = MailProcessorHandler(access_token)
    await handler.initialize()

    options = ProcessingOptions(
        mail_storage=mail_storage,
        attachment_handling=attachment_handling,
        output_format=output_format,
        save_directory=save_directory,
    )

    try:
        return await handler.process_mail(mail_data, options)
    finally:
        await handler.close()
