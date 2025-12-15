"""
Azure AD configuration management module.
Azure AD 앱 설정 및 토큰 관리를 담당합니다.
"""

import os
import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AzureConfig:
    """Azure AD 설정 관리 클래스"""

    def __init__(self, auth_db=None, client_id: Optional[str] = None):
        """
        Azure 설정 초기화

        Args:
            auth_db: AuthDatabase 인스턴스 (선택적)
            client_id: 사용할 client_id (None이면 환경변수에서 로드)
        """
        self.auth_db = auth_db
        self.db_path = auth_db.db_path if auth_db else "database/auth.db"

        # DB가 없으면 직접 생성 (하위 호환성)
        if not self.auth_db:
            from .auth_database import AuthDatabase
            self.auth_db = AuthDatabase(self.db_path)
            # AuthDatabase가 이미 초기화를 처리함

        # 우선순위: 1. 매개변수 2. 환경변수
        self.target_client_id = client_id or os.getenv("AZURE_CLIENT_ID")

        # DB에서 먼저 로드 시도
        if not self.load_config_from_db():
            # DB에 없으면 환경변수에서 로드 후 DB에 저장
            self.load_config_from_env()
            self.save_current_config_to_db()

    # ensure_database_exists 메서드 제거 - AuthDatabase가 처리

    def load_config_from_db(self) -> bool:
        """
        DB의 azure_app_config 테이블에서 설정 로드

        Returns:
            로드 성공 여부
        """
        if not self.target_client_id:
            return False

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM azure_app_config
                WHERE client_id = ?
            """, (self.target_client_id,))

            row = cursor.fetchone()
            if row:
                app_info = dict(row)

                # DB에서 로드한 설정 적용
                self.azure_client_id = app_info['client_id']
                self.azure_client_secret = app_info['client_secret']
                self.azure_tenant_id = app_info['tenant_id']
                self.azure_redirect_uri = app_info['redirect_uri']

                # OAuth endpoints
                self.authority = f"https://login.microsoftonline.com/{self.azure_tenant_id}"
                self.authorize_endpoint = f"{self.authority}/oauth2/v2.0/authorize"
                self.token_endpoint = f"{self.authority}/oauth2/v2.0/token"

                # Scopes 로드 (환경변수 폴백)
                self._load_scopes_from_env()

                logger.info(f"✅ Azure config loaded from DB: client_id={self.azure_client_id[:8]}...")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Failed to load config from DB: {e}")
            return False
        finally:
            conn.close()

    def load_config_from_env(self):
        """환경변수에서 Azure 설정 로드"""
        self.azure_client_id = os.getenv("AZURE_CLIENT_ID")
        self.azure_client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.azure_tenant_id = os.getenv("AZURE_TENANT_ID", "common")
        self.azure_redirect_uri = os.getenv("AZURE_REDIRECT_URI", "http://localhost:5000/callback")

        # OAuth endpoints
        self.authority = f"https://login.microsoftonline.com/{self.azure_tenant_id}"
        self.authorize_endpoint = f"{self.authority}/oauth2/v2.0/authorize"
        self.token_endpoint = f"{self.authority}/oauth2/v2.0/token"

        # Load scopes
        self._load_scopes_from_env()

        if self.azure_client_id and self.azure_client_secret:
            logger.info(f"✅ Azure config loaded from environment: client_id={self.azure_client_id[:8]}...")
        else:
            logger.warning("⚠️ Azure config not found in environment variables")

    def save_app_info(self, app_info: Dict[str, Any]) -> bool:
        """
        Azure AD 앱 정보를 데이터베이스에 저장

        Args:
            app_info: 앱 정보 딕셔너리

        Returns:
            성공 여부
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Check if app already exists
            cursor.execute(
                "SELECT client_id FROM azure_app_config WHERE client_id = ?",
                (app_info['client_id'],)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing app
                cursor.execute("""
                    UPDATE azure_app_config
                    SET client_id = ?, client_secret = ?, tenant_id = ?,
                        redirect_uri = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE client_id = ?
                """, (
                    app_info.get('client_id', app_info['client_id']),
                    app_info.get('client_secret'),
                    app_info.get('tenant_id', 'common'),
                    app_info.get('redirect_uri'),
                    app_info['client_id']
                ))
                logger.info(f"✅ Updated Azure app info: {app_info['client_id']}")
            else:
                # Insert new app
                cursor.execute("""
                    INSERT INTO azure_app_config
                    (client_id, client_id, client_secret, tenant_id, redirect_uri)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    app_info['client_id'],
                    app_info.get('client_id', app_info['client_id']),
                    app_info.get('client_secret'),
                    app_info.get('tenant_id', 'common'),
                    app_info.get('redirect_uri')
                ))
                logger.info(f"✅ Saved new Azure app info: {app_info['client_id']}")

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save app info: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_app_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Azure AD 앱 정보 조회

        Args:
            client_id: Azure AD 애플리케이션 ID

        Returns:
            앱 정보 딕셔너리 또는 None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM azure_app_config WHERE client_id = ?",
                (client_id,)
            )
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"❌ Failed to get app info: {e}")
            return None
        finally:
            conn.close()

    @property
    def client_id(self):
        """client_id 프로퍼티 (외부 호환성)"""
        return getattr(self, 'azure_client_id', None)

    @property
    def tenant_id(self):
        """tenant_id 프로퍼티 (외부 호환성)"""
        return getattr(self, 'azure_tenant_id', None)

    @property
    def client_secret(self):
        """client_secret 프로퍼티 (외부 호환성)"""
        return getattr(self, 'azure_client_secret', None)

    @property
    def redirect_uri(self):
        """redirect_uri 프로퍼티 (외부 호환성)"""
        return getattr(self, 'azure_redirect_uri', None)

    def _load_scopes_from_env(self):
        """환경변수에서 스코프 로드"""
        scopes_str = os.getenv("AZURE_SCOPES")
        if scopes_str:
            self.default_scopes = scopes_str.split()
        else:
            self.default_scopes = [
                "User.Read",
                "Mail.Read",
                "Mail.Send",
                "offline_access"
            ]

    def save_current_config_to_db(self) -> bool:
        """
        현재 설정을 DB에 저장

        Returns:
            성공 여부
        """
        if not self.azure_client_id:
            return False

        app_info = {
            'client_id': self.azure_client_id,
            'client_secret': self.azure_client_secret,
            'tenant_id': self.azure_tenant_id,
            'redirect_uri': self.azure_redirect_uri
        }

        return self.save_app_info(app_info)

    def switch_app(self, client_id: str) -> bool:
        """
        다른 Azure AD 앱으로 전환

        Args:
            client_id: 전환할 애플리케이션 ID

        Returns:
            전환 성공 여부
        """
        self.target_client_id = client_id
        if self.load_config_from_db():
            logger.info(f"✅ Switched to app: {client_id[:8]}...")
            return True

        logger.error(f"❌ Failed to switch to app: {client_id}")
        return False

    def list_all_apps(self) -> List[Dict[str, Any]]:
        """
        모든 Azure AD 앱 정보 조회

        Returns:
            앱 정보 리스트
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM azure_app_config ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Failed to list apps: {e}")
            return []
        finally:
            conn.close()