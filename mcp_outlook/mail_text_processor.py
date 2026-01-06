#!/usr/bin/env python3
"""
Mail Text Processor
메일과 첨부파일의 텍스트를 추출하고 통합 처리하는 모듈
메일 본문 + 첨부파일 텍스트 변환 및 통합
"""

import os
import sys
import tempfile
import shutil
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

# 상위 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_outlook.graph_mail_query import GraphMailQuery
from mcp_outlook.attachment_handler import AttachmentHandler
from mcp_file_handler.attachment_converter import AttachmentAPI


class MailTextProcessor:
    """메일과 첨부파일의 텍스트를 처리하는 프로세서"""

    def __init__(self, user_email: str, access_token: Optional[str] = None, temp_dir: Optional[str] = None):
        """
        초기화

        Args:
            user_email: User email for authentication
            access_token: Graph API 액세스 토큰 (선택사항, 없으면 AuthManager에서 가져옴)
            temp_dir: 임시 파일 저장 디렉토리 (None이면 시스템 임시 폴더)
        """
        self.user_email = user_email
        self.access_token = access_token
        self.mail_query = GraphMailQuery()
        self.attachment_handler = None  # Will be initialized with token
        self.attachment_converter = AttachmentAPI()

        # 임시 디렉토리 설정
        if temp_dir:
            self.temp_base = Path(temp_dir)
            self.temp_base.mkdir(parents=True, exist_ok=True)
        else:
            # 시스템 임시 디렉토리 사용
            self.temp_base = Path(tempfile.gettempdir()) / "mail_attachments"
            self.temp_base.mkdir(exist_ok=True)

        print(f"📁 임시 폴더: {self.temp_base}")

    async def initialize(self):
        """비동기 초기화"""
        await self.mail_query.initialize()

        # Get access token if not provided
        if not self.access_token:
            self.access_token = await self.mail_query._get_access_token(self.user_email)
            if not self.access_token:
                raise Exception(f"Failed to get access token for {self.user_email}")

        # Initialize attachment handler with token
        self.attachment_handler = AttachmentHandler(self.access_token)
        return True

    def _get_temp_dir(self, mail_id: str) -> Path:
        """메일별 임시 디렉토리 생성"""
        # 메일 ID 해시로 폴더명 생성 (너무 길면 문제 발생)
        mail_hash = hashlib.md5(mail_id.encode()).hexdigest()[:8]
        temp_dir = self.temp_base / f"mail_{mail_hash}"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir

    def _cleanup_temp_files(self, mail_id: str):
        """임시 파일 정리"""
        temp_dir = self._get_temp_dir(mail_id)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"🗑️ 임시 파일 정리: {temp_dir}")

    async def process_mail_v1_simple(self, mail_id: str) -> Dict[str, Any]:
        """
        버전 1: 단순 통합
        메일 본문 + 첨부파일 텍스트를 하나로 결합

        Returns:
            {
                "mail_id": "...",
                "subject": "...",
                "body": "메일 본문",
                "attachments": ["파일1.pdf", "파일2.docx"],
                "combined_text": "메일본문\n---\n첨부1텍스트\n---\n첨부2텍스트",
                "processing_info": {...}
            }
        """
        print(f"\n📧 [V1] 메일 처리 시작: {mail_id}")

        result = {
            "version": "v1_simple",
            "mail_id": mail_id,
            "timestamp": datetime.now().isoformat(),
            "status": "processing",
        }

        try:
            # 1. 메일 정보 조회
            print("  1️⃣ 메일 정보 조회 중...")
            mail_url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/messages/{mail_id}"
            mail_data = await self.mail_query._fetch_parallel_with_url(
                self.user_email, self.access_token, mail_url, 1
            )

            if not mail_data or not mail_data.get("value"):
                raise Exception("메일을 찾을 수 없습니다")

            mail = mail_data["value"][0] if isinstance(mail_data["value"], list) else mail_data["value"]

            result.update(
                {
                    "subject": mail.get("subject", "No Subject"),
                    "from": mail.get("from", {}).get("emailAddress", {}).get("address", ""),
                    "received": mail.get("receivedDateTime", ""),
                    "body": mail.get("body", {}).get("content", ""),
                    "body_type": mail.get("body", {}).get("contentType", "text"),
                    "has_attachments": mail.get("hasAttachments", False),
                }
            )

            # 2. 첨부파일 처리
            combined_texts = [result["body"]]  # 메일 본문부터 시작

            if result["has_attachments"]:
                print("  2️⃣ 첨부파일 처리 중...")

                # 첨부파일 목록 조회
                attachments = await self.attachment_handler.list_attachments(mail_id)
                print(f"     발견: {len(attachments)}개 첨부파일")

                result["attachments"] = []
                temp_dir = self._get_temp_dir(mail_id)

                for idx, att in enumerate(attachments, 1):
                    print(f"     [{idx}/{len(attachments)}] {att['name']}")

                    try:
                        # 다운로드
                        file_path = await self.attachment_handler.download_attachment(
                            mail_id, att["id"], str(temp_dir / att["name"])
                        )

                        # 텍스트 변환
                        converted_text = self.attachment_converter.convert_to_text(file_path)

                        # 결과 저장
                        result["attachments"].append(
                            {
                                "name": att["name"],
                                "size": att["size"],
                                "type": att["contentType"],
                                "text_length": len(converted_text),
                            }
                        )

                        # 통합 텍스트에 추가
                        combined_texts.append(f"\n\n--- 첨부파일: {att['name']} ---\n{converted_text}")

                    except Exception as e:
                        print(f"     ⚠️ 처리 실패: {e}")
                        result["attachments"].append({"name": att["name"], "error": str(e)})

            # 3. 텍스트 통합
            result["combined_text"] = "\n".join(combined_texts)
            result["total_length"] = len(result["combined_text"])
            result["status"] = "success"

            print(f"  ✅ 처리 완료: {result['total_length']:,} 문자")

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"  ❌ 오류: {e}")

        finally:
            # 임시 파일 정리 (옵션)
            # self._cleanup_temp_files(mail_id)
            pass

        return result

    async def process_mail_v2_structured(self, mail_id: str) -> Dict[str, Any]:
        """
        버전 2: 구조화된 통합
        메일과 첨부파일을 구조화하여 저장

        Returns:
            {
                "mail": {...},
                "attachments": [
                    {"name": "...", "text": "...", "metadata": {...}},
                    ...
                ],
                "search_index": "전체 검색용 텍스트",
                "summary": {...}
            }
        """
        print(f"\n📧 [V2] 구조화된 메일 처리: {mail_id}")

        result = {
            "version": "v2_structured",
            "mail_id": mail_id,
            "timestamp": datetime.now().isoformat(),
            "mail": {},
            "attachments": [],
            "search_index": "",
            "summary": {},
        }

        try:
            # 1. 메일 상세 정보
            mail_url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/messages/{mail_id}?$select=id,subject,from,toRecipients,receivedDateTime,body,hasAttachments,importance,categories"
            mail_data = await self.mail_query._fetch_parallel_with_url(
                self.user_email, self.access_token, mail_url, 1
            )
            mail = mail_data["value"][0] if isinstance(mail_data["value"], list) else mail_data["value"]

            result["mail"] = {
                "id": mail.get("id"),
                "subject": mail.get("subject"),
                "from": mail.get("from", {}).get("emailAddress", {}),
                "to": mail.get("toRecipients", []),
                "received": mail.get("receivedDateTime"),
                "body_text": mail.get("body", {}).get("content", ""),
                "body_type": mail.get("body", {}).get("contentType"),
                "importance": mail.get("importance"),
                "categories": mail.get("categories", []),
            }

            # 검색 인덱스 시작
            search_texts = [result["mail"]["subject"], result["mail"]["body_text"]]

            # 2. 첨부파일 상세 처리
            if mail.get("hasAttachments"):
                attachments = await self.attachment_handler.list_attachments(mail_id)
                temp_dir = self._get_temp_dir(mail_id)

                for att in attachments:
                    att_result = {
                        "id": att["id"],
                        "name": att["name"],
                        "size": att["size"],
                        "type": att["contentType"],
                        "processing": {},
                    }

                    try:
                        # 다운로드
                        file_path = await self.attachment_handler.download_attachment(
                            mail_id, att["id"], str(temp_dir / att["name"])
                        )

                        # 상세 변환 (메타데이터 포함)
                        conversion = self.attachment_converter.convert_with_metadata(file_path)

                        att_result.update(
                            {
                                "text": conversion["text"],
                                "metadata": conversion.get("metadata", {}),
                                "method": conversion.get("method"),
                                "processing": {
                                    "status": "success",
                                    "text_length": len(conversion["text"]),
                                    "extraction_method": conversion.get("method"),
                                },
                            }
                        )

                        search_texts.append(conversion["text"])

                    except Exception as e:
                        att_result["processing"] = {"status": "error", "error": str(e)}

                    result["attachments"].append(att_result)

            # 3. 검색 인덱스 생성
            result["search_index"] = "\n".join(search_texts)

            # 4. 요약 정보
            result["summary"] = {
                "total_attachments": len(result["attachments"]),
                "successful_conversions": len(
                    [a for a in result["attachments"] if a.get("processing", {}).get("status") == "success"]
                ),
                "total_text_length": len(result["search_index"]),
                "mail_text_length": len(result["mail"]["body_text"]),
                "attachment_text_length": sum([len(a.get("text", "")) for a in result["attachments"]]),
            }

            print(f"  ✅ 구조화 완료: {result['summary']}")

        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ 오류: {e}")

        return result

    async def process_mail_v3_separated(self, mail_id: str, keep_files: bool = False) -> Dict[str, Any]:
        """
        버전 3: 분리 저장
        메일과 첨부파일을 별도로 저장하되 연결 정보 유지

        Args:
            mail_id: 메일 ID
            keep_files: 변환 후 파일 유지 여부

        Returns:
            {
                "mail_file": "mail_12345.json",
                "attachment_files": ["att1_12345.txt", "att2_12345.txt"],
                "index_file": "index_12345.json",
                "temp_directory": "/tmp/mail_attachments/mail_12345/"
            }
        """
        print(f"\n📧 [V3] 분리 저장 처리: {mail_id}")

        temp_dir = self._get_temp_dir(mail_id)
        result = {
            "version": "v3_separated",
            "mail_id": mail_id,
            "timestamp": datetime.now().isoformat(),
            "temp_directory": str(temp_dir),
            "files": {},
        }

        try:
            # 1. 메일 정보 저장
            mail_url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/messages/{mail_id}"
            mail_data = await self.mail_query._fetch_parallel_with_url(
                self.user_email, self.access_token, mail_url, 1
            )
            mail = mail_data["value"][0] if isinstance(mail_data["value"], list) else mail_data["value"]

            mail_file = temp_dir / f"mail_{mail_id[:8]}.json"
            with open(mail_file, "w", encoding="utf-8") as f:
                json.dump(mail, f, ensure_ascii=False, indent=2)

            result["files"]["mail"] = str(mail_file)
            print(f"  📄 메일 저장: {mail_file.name}")

            # 2. 첨부파일 개별 처리
            if mail.get("hasAttachments"):
                attachments = await self.attachment_handler.list_attachments(mail_id)
                result["files"]["attachments"] = []

                att_dir = temp_dir / "attachments"
                att_dir.mkdir(exist_ok=True)

                for idx, att in enumerate(attachments):
                    # 원본 다운로드
                    original_path = att_dir / att["name"]
                    await self.attachment_handler.download_attachment(mail_id, att["id"], str(original_path))

                    # 텍스트 변환 및 저장
                    try:
                        text = self.attachment_converter.convert_to_text(str(original_path))
                        text_file = att_dir / f"{att['name']}.txt"
                        with open(text_file, "w", encoding="utf-8") as f:
                            f.write(text)

                        result["files"]["attachments"].append(
                            {
                                "original": str(original_path),
                                "text": str(text_file),
                                "name": att["name"],
                                "size": att["size"],
                            }
                        )

                        print(f"  📎 첨부 {idx+1}: {att['name']} → {text_file.name}")

                    except Exception as e:
                        print(f"  ⚠️ 변환 실패 ({att['name']}): {e}")

            # 3. 인덱스 파일 생성
            index_file = temp_dir / f"index_{mail_id[:8]}.json"
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            result["files"]["index"] = str(index_file)
            print(f"  📑 인덱스 저장: {index_file.name}")

            # 4. 파일 정리 (선택적)
            if not keep_files:
                result["cleanup_scheduled"] = True
                # 실제 정리는 나중에 수행
            else:
                result["cleanup_scheduled"] = False

        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ 오류: {e}")

        return result

    async def process_mail_batch(
        self, mail_ids: List[str], version: str = "v1", parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """
        여러 메일 일괄 처리

        Args:
            mail_ids: 메일 ID 리스트
            version: 처리 버전 ("v1", "v2", "v3")
            parallel: 병렬 처리 여부

        Returns:
            처리 결과 리스트
        """
        print(f"\n📬 일괄 처리: {len(mail_ids)}개 메일 (버전: {version})")

        # 버전별 처리 함수 선택
        process_func = {
            "v1": self.process_mail_v1_simple,
            "v2": self.process_mail_v2_structured,
            "v3": self.process_mail_v3_separated,
        }.get(version, self.process_mail_v1_simple)

        if parallel:
            # 병렬 처리
            tasks = [process_func(mail_id) for mail_id in mail_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 순차 처리
            results = []
            for mail_id in mail_ids:
                result = await process_func(mail_id)
                results.append(result)

        # 결과 요약
        success_count = len([r for r in results if isinstance(r, dict) and r.get("status") != "error"])
        print(f"\n✅ 완료: {success_count}/{len(mail_ids)} 성공")

        return results

    async def search_in_processed_mails(
        self, keyword: str, processed_mails: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        처리된 메일에서 키워드 검색

        Args:
            keyword: 검색 키워드
            processed_mails: 처리된 메일 데이터 리스트

        Returns:
            매칭된 결과
        """
        keyword_lower = keyword.lower()
        results = []

        for mail_data in processed_mails:
            matches = []

            # V1 형식
            if "combined_text" in mail_data:
                if keyword_lower in mail_data["combined_text"].lower():
                    matches.append(
                        {"type": "combined", "context": self._extract_context(mail_data["combined_text"], keyword)}
                    )

            # V2 형식
            elif "search_index" in mail_data:
                if keyword_lower in mail_data["search_index"].lower():
                    # 메일 본문에서 찾기
                    if keyword_lower in mail_data.get("mail", {}).get("body_text", "").lower():
                        matches.append(
                            {
                                "type": "mail_body",
                                "context": self._extract_context(mail_data["mail"]["body_text"], keyword),
                            }
                        )

                    # 첨부파일에서 찾기
                    for att in mail_data.get("attachments", []):
                        if keyword_lower in att.get("text", "").lower():
                            matches.append(
                                {
                                    "type": "attachment",
                                    "name": att["name"],
                                    "context": self._extract_context(att["text"], keyword),
                                }
                            )

            if matches:
                results.append(
                    {
                        "mail_id": mail_data.get("mail_id"),
                        "subject": mail_data.get("subject") or mail_data.get("mail", {}).get("subject"),
                        "matches": matches,
                    }
                )

        return results

    def _extract_context(self, text: str, keyword: str, context_size: int = 100) -> str:
        """키워드 주변 문맥 추출"""
        keyword_lower = keyword.lower()
        text_lower = text.lower()

        idx = text_lower.find(keyword_lower)
        if idx == -1:
            return ""

        start = max(0, idx - context_size)
        end = min(len(text), idx + len(keyword) + context_size)

        context = text[start:end]
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context

    def get_temp_stats(self) -> Dict[str, Any]:
        """임시 폴더 통계"""
        stats = {
            "base_directory": str(self.temp_base),
            "exists": self.temp_base.exists(),
            "mail_folders": [],
            "total_size": 0,
        }

        if self.temp_base.exists():
            for folder in self.temp_base.iterdir():
                if folder.is_dir():
                    folder_size = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
                    stats["mail_folders"].append(
                        {"name": folder.name, "files": len(list(folder.rglob("*"))), "size": folder_size}
                    )
                    stats["total_size"] += folder_size

        stats["total_folders"] = len(stats["mail_folders"])
        return stats

    def cleanup_all_temp(self):
        """모든 임시 파일 정리"""
        if self.temp_base.exists():
            shutil.rmtree(self.temp_base)
            self.temp_base.mkdir(exist_ok=True)
            print(f"🗑️ 모든 임시 파일 정리 완료: {self.temp_base}")


async def main():
    """테스트 및 예제"""
    print("Mail-Attachment Integrator Test")
    print("=" * 60)

    # 실제 사용 시 액세스 토큰 필요
    # integrator = MailAttachmentIntegrator(access_token="YOUR_TOKEN")
    # await integrator.initialize()

    # 예제 사용법
    """
    # 1. 단일 메일 처리 (V1 - 단순 통합)
    result = await integrator.process_mail_v1_simple("mail_id_here")
    print(result['combined_text'])

    # 2. 구조화된 처리 (V2)
    result = await integrator.process_mail_v2_structured("mail_id_here")
    for att in result['attachments']:
        print(f"첨부파일: {att['name']} - {len(att.get('text', ''))} 문자")

    # 3. 분리 저장 (V3)
    result = await integrator.process_mail_v3_separated("mail_id_here", keep_files=True)
    print(f"파일 저장 위치: {result['temp_directory']}")

    # 4. 일괄 처리
    mail_ids = ["id1", "id2", "id3"]
    results = await integrator.process_mail_batch(mail_ids, version="v2")

    # 5. 검색
    search_results = await integrator.search_in_processed_mails("계약서", results)
    for sr in search_results:
        print(f"메일: {sr['subject']}")
        for match in sr['matches']:
            print(f"  - {match['type']}: {match['context']}")
    """


if __name__ == "__main__":
    asyncio.run(main())
