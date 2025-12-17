"""
Authentication Manager
다중 사용자 인증 및 토큰 관리 + 콜백 서버 생애주기 관리
"""

import logging
import asyncio
import webbrowser
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

from .auth_service import AuthService
from .auth_database import AuthDatabase
from .azure_config import AzureConfig

logger = logging.getLogger(__name__)


class AuthManager:
    """인증 매니저 - 다중 사용자 관리 및 콜백 서버 통합"""

    def __init__(self, db_path: Optional[str] = None, app_id: Optional[str] = None):
        """
        인증 매니저 초기화 - 모든 컴포넌트의 중앙 관리자

        Args:
            db_path: 데이터베이스 경로 (None이면 환경변수 또는 기본값 사용)
            app_id: 사용할 Azure AD 앱 ID (선택적)
        """
        # DB 경로 결정 (환경변수 > 파라미터 > 기본값)
        import os
        if db_path is None:
            # Use absolute path for database
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.getenv('DB_PATH', os.path.join(base_dir, 'database', 'auth.db'))

        # 1. DB 인스턴스 생성 (단일 인스턴스)
        self.auth_db = AuthDatabase(db_path)

        # 2. Config 인스턴스 생성 (DB 공유)
        self.config = AzureConfig(self.auth_db, app_id)

        # 3. AuthService 생성 (DB와 Config 공유)
        self.auth_service = AuthService(self.auth_db, self.config)

        # 4. 콜백 서버 인스턴스 (필요시 생성)
        self.callback_server = None

    def start_authentication(self) -> Dict[str, str]:
        """
        새 사용자 인증 시작 - URL 생성

        Returns:
            Dict: 인증 정보
                - auth_url: Azure AD 인증 URL
                - state: 보안 검증용 state
        """
        return self.auth_service.start_auth_flow(force_new=True)

    async def get_token(self, email: str) -> Optional[Dict[str, Any]]:
        """
        특정 사용자의 토큰 조회

        Args:
            email: 사용자 이메일

        Returns:
            토큰 정보 또는 None
        """
        token_info = self.auth_db.get_token(email)

        if not token_info:
            logger.warning(f"No token found for {email}")
            return None

        return {
            'email': email,
            'access_token': token_info['access_token'],
            'refresh_token': token_info.get('refresh_token'),
            'expires_at': token_info['expires_at'],
            'is_expired': self.auth_service.is_token_expired(token_info['expires_at'])
        }

    async def refresh_token(self, email: str) -> Dict[str, Any]:
        """
        특정 사용자의 토큰 갱신

        Args:
            email: 사용자 이메일

        Returns:
            갱신 결과
        """
        try:
            # 기존 토큰 조회
            token_info = self.auth_db.get_token(email)

            if not token_info:
                return {
                    'status': 'error',
                    'error': 'No token found',
                    'message': f'No token found for {email}'
                }

            if not token_info.get('refresh_token'):
                return {
                    'status': 'error',
                    'error': 'No refresh token',
                    'message': 'Refresh token not available, re-authentication required'
                }

            # 리프레시 토큰 만료 확인
            created_at = token_info.get('created_at', token_info.get('updated_at'))
            if self.auth_service.is_refresh_token_expired(created_at):
                return {
                    'status': 'reauth_required',
                    'error': 'Refresh token expired',
                    'message': 'Refresh token expired, re-authentication required'
                }

            # 토큰 갱신
            new_tokens = await self.auth_service.refresh_tokens(token_info['refresh_token'])

            # DB 업데이트
            success = self.auth_db.update_token(email, new_tokens)

            if success:
                logger.info(f"Token refreshed for {email}")
                return {
                    'status': 'success',
                    'email': email,
                    'access_token': new_tokens['access_token'],
                    'expires_at': new_tokens['expires_at'],
                    'message': 'Token refreshed successfully'
                }
            else:
                raise Exception("Failed to update token in database")

        except Exception as e:
            logger.error(f"Token refresh failed for {email}: {str(e)}")

            # refresh token이 revoke된 경우
            if 'invalid_grant' in str(e).lower() or 'expired' in str(e).lower():
                return {
                    'status': 'reauth_required',
                    'error': str(e),
                    'message': 'Re-authentication required'
                }

            return {
                'status': 'error',
                'error': str(e)
            }

    async def validate_and_refresh_token(self, email: str) -> Optional[str]:
        """
        토큰 유효성 확인 및 필요시 자동 갱신

        Args:
            email: 사용자 이메일

        Returns:
            유효한 액세스 토큰 또는 None
        """
        token_info = self.auth_db.get_token(email)

        if not token_info:
            logger.error(f"No token found for {email}")
            return None

        # 토큰이 유효한 경우
        if not self.auth_service.is_token_expired(token_info['expires_at']):
            return token_info['access_token']

        # 토큰 갱신 시도
        logger.info(f"Token expired for {email}, attempting refresh")
        refresh_result = await self.refresh_token(email)

        if refresh_result['status'] == 'success':
            return refresh_result['access_token']

        logger.error(f"Failed to get valid token for {email}")
        return None

    def list_users(self) -> List[Dict[str, Any]]:
        """
        모든 인증된 사용자 목록

        Returns:
            사용자 리스트
        """
        users = self.auth_db.list_users()

        # 각 사용자의 토큰 상태 추가
        for user in users:
            token_info = self.auth_db.get_token(user['email'])
            if token_info:
                user['has_token'] = True
                user['token_expired'] = self.auth_service.is_token_expired(token_info['expires_at'])
                user['has_refresh_token'] = bool(token_info.get('refresh_token'))
            else:
                user['has_token'] = False

        return users


    def remove_user(self, email: str) -> bool:
        """
        사용자 제거 (토큰 삭제)

        Args:
            email: 사용자 이메일

        Returns:
            성공 여부
        """
        success = self.auth_db.delete_token(email)

        if success:
            logger.info(f"User {email} removed")
        else:
            logger.error(f"Failed to remove user {email}")

        return success

    def cleanup_expired_tokens(self) -> int:
        """
        만료된 토큰 정리

        Returns:
            정리된 토큰 수
        """
        count = self.auth_db.cleanup_expired_tokens()
        logger.info(f"Cleaned up {count} expired tokens")
        return count

    def get_token_status(self, email: str) -> Dict[str, Any]:
        """
        사용자 토큰 상태 조회

        Args:
            email: 사용자 이메일

        Returns:
            토큰 상태 정보
        """
        token_info = self.auth_db.get_token(email)

        if not token_info:
            return {
                'status': 'not_found',
                'email': email,
                'message': 'No token found'
            }

        # 액세스 토큰 상태
        access_expired = self.auth_service.is_token_expired(token_info['expires_at'])

        # 리프레시 토큰 상태
        has_refresh = bool(token_info.get('refresh_token'))
        refresh_expired = False
        if has_refresh:
            created_at = token_info.get('created_at', token_info.get('updated_at'))
            refresh_expired = self.auth_service.is_refresh_token_expired(created_at)

        return {
            'status': 'found',
            'email': email,
            'access_token_expired': access_expired,
            'access_token_expires_at': token_info['expires_at'],
            'has_refresh_token': has_refresh,
            'refresh_token_expired': refresh_expired,
            'needs_refresh': access_expired and has_refresh and not refresh_expired,
            'needs_reauth': not has_refresh or refresh_expired
        }

    def is_callback_server_running(self) -> bool:
        """
        콜백 서버 실행 상태 확인

        Returns:
            서버 실행 중이면 True, 아니면 False
        """
        return self.callback_server is not None and self.callback_server.is_running()

    async def ensure_callback_server(self, port: int = 5000) -> bool:
        """
        콜백 서버가 실행 중인지 확인하고, 필요시 시작

        Args:
            port: 서버 포트 (기본 5000)

        Returns:
            서버가 실행 중이거나 성공적으로 시작되면 True
        """
        # CallbackServer 인스턴스가 없으면 생성
        if self.callback_server is None:
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, parent_dir)
            from callback_server import CallbackServer

            self.callback_server = CallbackServer(auth_manager=self, port=port)

        # 이미 실행 중인지 확인
        if self.callback_server.is_running():
            logger.info(f"Callback server already running on port {port}")
            return True

        # 포트가 다른 프로세스에서 사용 중인지 확인
        if not self.callback_server.check_port_availability():
            logger.warning(f"Port {port} is already in use by another process")
            # 외부 콜백 서버가 실행 중일 수 있으므로 True 반환
            return True

        # 서버 시작
        try:
            await self.callback_server.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start callback server: {e}")
            return False

    async def stop_callback_server(self):
        """콜백 서버 종료"""
        if self.callback_server and self.callback_server.is_running():
            await self.callback_server.stop()
            logger.info("Callback server stopped")

    async def authenticate_with_browser(self, timeout: int = 300, port: int = 5000) -> Dict[str, Any]:
        """
        브라우저를 통한 완전한 인증 플로우

        Args:
            timeout: 인증 대기 시간 (초, 기본 5분)
            port: 콜백 서버 포트 (기본 5000)

        Returns:
            인증 결과
        """
        server_was_running = self.is_callback_server_running()

        try:
            # 1. 콜백 서버 상태 확인 및 시작
            logger.info("Checking callback server status...")
            if not await self.ensure_callback_server(port):
                return {
                    'status': 'error',
                    'error': 'Failed to start callback server'
                }

            # 2. 인증 URL 생성
            auth_info = self.start_authentication()
            logger.info(f"Authentication URL generated with state: {auth_info['state'][:10]}...")

            # 3. 브라우저 열기
            logger.info("Opening browser for authentication")
            try:
                webbrowser.open(auth_info['auth_url'])
                logger.info("Browser opened successfully")
            except Exception as e:
                logger.warning(f"Could not open browser: {e}")
                print(f"\n⚠️ Please manually visit: {auth_info['auth_url']}")

            # 4. 인증 완료 대기
            logger.info(f"Waiting for authentication (timeout: {timeout}s)")

            # CallbackServer의 인증 대기 기능 사용
            if self.callback_server:
                # 인증 이벤트 초기화
                self.callback_server.reset_auth_event()

                # 인증 완료 대기
                authenticated_email = await self.callback_server.wait_for_auth(timeout)

                if authenticated_email:
                    # 인증된 사용자 정보 조회
                    users = self.list_users()
                    user = next((u for u in users if u['email'] == authenticated_email), None)

                    if user:
                        logger.info(f"Authentication successful for {authenticated_email}")
                        return {
                            'status': 'success',
                            'email': authenticated_email,
                            'user': user
                        }
                    else:
                        raise Exception(f"User {authenticated_email} authenticated but not found in DB")
                else:
                    raise asyncio.TimeoutError("Authentication timeout")

            else:
                # 외부 서버 사용 중 - DB 폴링 방식
                start_time = asyncio.get_event_loop().time()
                initial_users = self.list_users()
                initial_emails = {u['email'] for u in initial_users}

                while (asyncio.get_event_loop().time() - start_time) < timeout:
                    await asyncio.sleep(2)  # 2초마다 확인
                    current_users = self.list_users()
                    current_emails = {u['email'] for u in current_users}

                    # 새로운 사용자가 추가되었는지 확인
                    new_emails = current_emails - initial_emails
                    if new_emails:
                        latest_email = list(new_emails)[0]
                        logger.info(f"Authentication successful for {latest_email}")
                        user = next(u for u in current_users if u['email'] == latest_email)
                        return {
                            'status': 'success',
                            'email': latest_email,
                            'user': user
                        }

                raise asyncio.TimeoutError("Authentication timeout")

        except asyncio.TimeoutError:
            logger.error("Authentication timeout")
            return {
                'status': 'timeout',
                'error': 'Authentication timeout'
            }
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            # 6. 서버가 원래 실행 중이지 않았다면 정리
            if not server_was_running and self.is_callback_server_running():
                logger.info("Stopping callback server (was not running before)")
                await self.stop_callback_server()

    async def close(self):
        """리소스 정리"""
        # 콜백 서버 정리
        await self.stop_callback_server()

        # AuthService 정리
        await self.auth_service.close()

        logger.info("Auth manager closed")


# 사용 예시
async def example_usage():
    """AuthManager 사용 예시"""
    import asyncio

    manager = AuthManager()

    try:
        # 1. 새 사용자 인증
        print("\n=== Authenticating new user ===")
        auth_result = await manager.authenticate()

        if auth_result['status'] == 'success':
            print(f"✅ Authenticated as: {auth_result['email']}")

        # 2. 사용자 목록
        print("\n=== User list ===")
        users = manager.list_users()
        for user in users:
            print(f"- {user['email']}: Token valid={not user.get('token_expired', True)}")

        # 3. 토큰 갱신
        if manager.current_user:
            print(f"\n=== Refreshing token for {manager.current_user} ===")
            refresh_result = await manager.refresh_token(manager.current_user)
            print(f"Result: {refresh_result['status']}")

        # 4. 유효한 토큰 가져오기
        print("\n=== Getting valid token ===")
        token = await manager.get_current_token()
        if token:
            print(f"✅ Got valid token: {token[:20]}...")

    finally:
        await manager.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())