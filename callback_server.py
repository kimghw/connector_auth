#!/usr/bin/env python3
"""
OAuth Callback Server
Azure AD 인증 콜백을 처리하는 웹서버입니다.
클래스 기반으로 리팩토링하여 AuthManager에서 사용할 수 있습니다.
"""

import asyncio
import json
import socket
import logging
from aiohttp import web
from urllib.parse import parse_qs
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CallbackServer:
    """OAuth 콜백 서버 클래스"""

    def __init__(self, auth_manager=None, port: int = 5000):
        """
        콜백 서버 초기화

        Args:
            auth_manager: AuthManager 인스턴스 (옵션)
            port: 서버 포트 (기본 5000)
        """
        self.auth_manager = auth_manager
        self.port = port
        self.app = None
        self.runner = None
        self.site = None
        self.auth_completed = asyncio.Event()
        self.authenticated_email = None

        # AuthManager가 없으면 독립 실행 모드
        if not auth_manager:
            from auth import AuthManager
            self.auth_manager = AuthManager()
            self.standalone_mode = True
        else:
            self.standalone_mode = False

        # AuthService는 AuthManager에서 가져옴
        self.auth_service = self.auth_manager.auth_service

    def is_running(self) -> bool:
        """서버 실행 상태 확인"""
        return self.site is not None

    def check_port_availability(self) -> bool:
        """
        포트 사용 가능 여부 확인

        Returns:
            포트가 사용 가능하면 True
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', self.port))
            sock.close()
            return True
        except OSError:
            return False

    async def handle_callback(self, request):
        """OAuth 콜백 처리"""
        # 전체 URL 로그 (안전한 방식)
        logger.info(f"Callback received - Path: {request.path}")
        logger.info(f"Query string: {request.query_string}")

        query_params = parse_qs(request.query_string)

        # Get authorization code and state
        code = query_params.get('code', [None])[0]
        state = query_params.get('state', [None])[0]
        error = query_params.get('error', [None])[0]
        error_description = query_params.get('error_description', [None])[0]

        if error:
            html_content = f"""
            <html>
            <head>
                <title>Authentication Failed</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }}
                    .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: auto; }}
                    h1 {{ color: #d73027; }}
                    .error {{ background: #fee; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .button {{ background: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; }}
                    .button:hover {{ background: #357ae8; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Authentication Failed</h1>
                    <div class="error">
                        <strong>Error:</strong> {error}<br>
                        <strong>Description:</strong> {error_description or 'No additional information'}
                    </div>
                    <p>Please try again or contact your administrator if the problem persists.</p>
                    <a href="/" class="button">Try Again</a>
                </div>
            </body>
            </html>
            """
            return web.Response(text=html_content, content_type='text/html', status=400)

        if not code:
            return web.Response(text="Missing authorization code", status=400)

        logger.info(f"Processing callback with state: {state[:10]}...")

        try:
            # Exchange code for tokens
            token_response = await self.auth_service.complete_auth_flow(code, state)

            # complete_auth_flow는 성공 시 user_email을 직접 반환
            user_email = token_response.get('user_email')

            if user_email:
                logger.info(f"✅ Authentication successful for user: {user_email}")

                # 인증 완료 이벤트 설정
                self.authenticated_email = user_email
                self.auth_completed.set()

                # Success page with auto-close script
                html_content = f"""
                <html>
                <head>
                    <title>Authentication Successful</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }}
                        .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: auto; }}
                        h1 {{ color: #27ae60; }}
                        .user-info {{ background: #e8f6ef; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                        .message {{ color: #666; margin-top: 20px; }}
                    </style>
                    <script>
                        setTimeout(function() {{
                            window.close();
                        }}, 3000);
                    </script>
                </head>
                <body>
                    <div class="container">
                        <h1>✅ Authentication Successful!</h1>
                        <div class="user-info">
                            <strong>Logged in as:</strong> {user_email}
                        </div>
                        <p class="message">This window will close automatically in 3 seconds...</p>
                        <p class="message">You can now return to your application.</p>
                    </div>
                </body>
                </html>
                """
                return web.Response(text=html_content, content_type='text/html')

            else:
                # Authentication failed - user_email이 없는 경우
                error_msg = "Failed to authenticate - no user email returned"
                logger.error(f"Authentication failed: {token_response}")
                html_content = f"""
                <html>
                <head>
                    <title>Authentication Failed</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .error {{ color: red; }}
                    </style>
                </head>
                <body>
                    <h1>Authentication Failed</h1>
                    <p class="error">{error_msg}</p>
                    <p><a href="/">Try Again</a></p>
                </body>
                </html>
                """
                return web.Response(text=html_content, content_type='text/html', status=401)

        except Exception as e:
            logger.error(f"Error during callback processing: {e}")
            return web.Response(text=f"Server error: {str(e)}", status=500)

    async def handle_root(self, request):
        """Root endpoint - shows server status"""
        html_content = """
        <html>
        <head>
            <title>Azure OAuth Callback Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
                .container { background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: auto; }
                h1 { color: #4285f4; }
                .status { background: #e8f5e9; padding: 20px; border-radius: 5px; margin: 20px 0; }
                .info { margin: 10px 0; }
                code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 Azure OAuth Callback Server</h1>
                <div class="status">
                    <strong>✅ Server is running</strong>
                </div>
                <div class="info">
                    <strong>Callback URL:</strong> <code>http://localhost:5000/callback</code>
                </div>
                <div class="info">
                    <strong>Status:</strong> Ready to receive authentication callbacks
                </div>
                <p>This server handles OAuth 2.0 callbacks from Azure AD.</p>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html_content, content_type='text/html')

    async def handle_status(self, request):
        """Status endpoint - returns JSON status"""
        status = {
            'status': 'running',
            'port': self.port,
            'callback_url': f'http://localhost:{self.port}/callback',
            'standalone_mode': self.standalone_mode
        }
        return web.json_response(status)

    async def init_app(self):
        """Initialize the web application"""
        self.app = web.Application()

        # Add routes
        self.app.router.add_get('/callback', self.handle_callback)
        self.app.router.add_get('/', self.handle_root)
        self.app.router.add_get('/status', self.handle_status)

        # Add cleanup handler
        self.app.on_cleanup.append(self._cleanup)

        return self.app

    async def _cleanup(self, app):
        """Cleanup on shutdown"""
        if self.standalone_mode:
            await self.auth_manager.close()
        logger.info("Server shutdown complete")

    async def start(self):
        """서버 시작"""
        if self.is_running():
            logger.warning("Server already running")
            return

        # 포트 확인
        if not self.check_port_availability():
            logger.warning(f"Port {self.port} is already in use")
            raise OSError(f"Port {self.port} is already in use")

        # 앱 초기화
        await self.init_app()

        # 서버 시작
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, 'localhost', self.port)
        await self.site.start()

        logger.info(f"Callback server started on http://localhost:{self.port}")

    async def stop(self):
        """서버 종료"""
        if self.site:
            await self.site.stop()
            self.site = None
            logger.info("Server site stopped")

        if self.runner:
            await self.runner.cleanup()
            self.runner = None
            logger.info("Server runner cleaned up")

    async def wait_for_auth(self, timeout: int = 300):
        """
        인증 완료 대기

        Args:
            timeout: 대기 시간 (초)

        Returns:
            인증된 이메일 또는 None
        """
        try:
            await asyncio.wait_for(self.auth_completed.wait(), timeout=timeout)
            return self.authenticated_email
        except asyncio.TimeoutError:
            logger.warning("Authentication timeout")
            return None

    def reset_auth_event(self):
        """인증 이벤트 초기화"""
        self.auth_completed.clear()
        self.authenticated_email = None


# 독립 실행을 위한 메인 함수
async def run_standalone_server():
    """독립 실행 모드로 서버 실행"""
    port = int(os.getenv('CALLBACK_PORT', '5000'))

    print("\n" + "="*60)
    print(" Azure Authentication Callback Server")
    print("="*60)
    print(f"🚀 Starting server on http://localhost:{port}")
    print(f"📍 Callback URL: http://localhost:{port}/callback")
    print("="*60)
    print("\nPress Ctrl+C to stop the server\n")

    # 서버 생성 및 시작
    server = CallbackServer(port=port)

    try:
        await server.start()

        # 서버 유지
        while True:
            await asyncio.sleep(3600)

    except KeyboardInterrupt:
        print("\n\nShutting down server...")
    finally:
        await server.stop()
        if server.standalone_mode:
            await server.auth_manager.close()


def main():
    """Main function for standalone execution"""
    try:
        asyncio.run(run_standalone_server())
    except KeyboardInterrupt:
        print("\nServer stopped by user")


if __name__ == '__main__':
    main()