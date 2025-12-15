"""
Session Manager for MCP Server
Manages user sessions with GraphMailQuery and GraphMailClient instances
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import logging

from mcp_outlook.graph_mail_query import GraphMailQuery
from mcp_outlook.graph_mail_client import GraphMailClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Session:
    """
    User session containing GraphMail instances and authentication state
    """

    def __init__(self, user_email: str):
        """
        Initialize a new session for a user

        Args:
            user_email: User's email address (session identifier)
        """
        self.user_email = user_email
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_token: Optional[str] = None

        # Create user-specific instances
        self.graph_mail_query = GraphMailQuery()
        self.graph_mail_client = GraphMailClient(user_email=user_email)

        # Session state
        self.is_active = True
        self.initialized = False

        logger.info(f"Session created for user: {user_email}")

    async def initialize(self, access_token: Optional[str] = None) -> bool:
        """
        Initialize the session with authentication
        If no access token provided, try to get from DB and refresh if needed

        Args:
            access_token: Optional access token to use

        Returns:
            True if initialization successful
        """
        try:
            # If no access token provided, try to get from AuthManager
            if not access_token:
                # AuthManager will handle DB lookup and refresh
                from auth.auth_manager import AuthManager
                auth_manager = AuthManager()

                # Try to get valid token (will refresh if expired)
                access_token = await auth_manager.validate_and_refresh_token(self.user_email)

                if not access_token:
                    logger.warning(f"No valid token found in DB for user: {self.user_email}")
                    # Don't fail here - user might provide token later
                    # return False

            # Store the access token if we got one
            if access_token:
                self.access_token = access_token
                self.graph_mail_client.access_token = access_token

            # Initialize GraphMailClient
            success = await self.graph_mail_client.initialize(self.user_email)
            if success:
                self.initialized = True
                logger.info(f"Session initialized for user: {self.user_email}")
            else:
                logger.error(f"Failed to initialize GraphMailClient for user: {self.user_email}")

            return success

        except Exception as e:
            logger.error(f"Session initialization error for {self.user_email}: {str(e)}")
            return False

    async def refresh_token(self) -> bool:
        """
        Refresh the access token using refresh token from DB

        Returns:
            True if token refreshed successfully
        """
        try:
            from auth.auth_manager import AuthManager
            auth_manager = AuthManager()

            # Refresh token using AuthManager
            new_token = await auth_manager.validate_and_refresh_token(self.user_email)

            if new_token:
                self.access_token = new_token
                if hasattr(self, 'graph_mail_client'):
                    self.graph_mail_client.access_token = new_token
                logger.info(f"Token refreshed for session: {self.user_email}")
                return True
            else:
                logger.error(f"Failed to refresh token for session: {self.user_email}")
                return False

        except Exception as e:
            logger.error(f"Error refreshing token for {self.user_email}: {str(e)}")
            return False

    def update_access_time(self):
        """Update last accessed timestamp"""
        self.last_accessed = datetime.now()

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """
        Check if session has expired

        Args:
            timeout_minutes: Session timeout in minutes

        Returns:
            True if session is expired
        """
        if not self.is_active:
            return True

        time_since_access = datetime.now() - self.last_accessed
        return time_since_access > timedelta(minutes=timeout_minutes)

    def invalidate_token(self):
        """Invalidate the access token and mark session for removal"""
        self.access_token = None
        self.is_active = False
        logger.info(f"Token invalidated for session: {self.user_email}")

    async def cleanup(self):
        """Clean up session resources"""
        try:
            # Close GraphMailQuery resources
            if hasattr(self.graph_mail_query, 'close'):
                await self.graph_mail_query.close()

            # Close GraphMailClient resources
            if hasattr(self.graph_mail_client, 'close'):
                await self.graph_mail_client.close()

            self.is_active = False
            logger.info(f"Session cleaned up for user: {self.user_email}")

        except Exception as e:
            logger.error(f"Error cleaning up session for {self.user_email}: {str(e)}")


class SessionManager:
    """
    Manages all user sessions with automatic cleanup
    """

    def __init__(self, session_timeout_minutes: int = 30, cleanup_interval_minutes: int = 5):
        """
        Initialize SessionManager

        Args:
            session_timeout_minutes: Minutes before a session expires
            cleanup_interval_minutes: Interval for cleanup task
        """
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = session_timeout_minutes
        self.cleanup_interval = cleanup_interval_minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        logger.info(f"SessionManager initialized with {session_timeout_minutes}min timeout")

    async def start(self):
        """Start the session manager and cleanup task"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            logger.info("SessionManager cleanup task started")

    async def stop(self):
        """Stop the session manager and clean up all sessions"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Clean up all sessions
        async with self._lock:
            for session in self.sessions.values():
                await session.cleanup()
            self.sessions.clear()

        logger.info("SessionManager stopped and all sessions cleaned up")

    async def get_or_create_session(self, user_email: str, access_token: Optional[str] = None) -> Session:
        """
        Get existing session or create a new one for the user

        Args:
            user_email: User's email address
            access_token: Optional access token for new sessions

        Returns:
            User session
        """
        async with self._lock:
            # Check if session exists and is valid
            if user_email in self.sessions:
                session = self.sessions[user_email]

                # Check if session is still valid
                if not session.is_expired(self.session_timeout):
                    session.update_access_time()
                    logger.debug(f"Returning existing session for: {user_email}")
                    return session
                else:
                    # Session expired, clean it up
                    await session.cleanup()
                    del self.sessions[user_email]
                    logger.info(f"Expired session removed for: {user_email}")

            # Create new session
            session = Session(user_email)

            # Initialize if not already initialized
            if not session.initialized:
                await session.initialize(access_token)

            self.sessions[user_email] = session
            logger.info(f"New session created for: {user_email}")

            return session

    async def get_session(self, user_email: str) -> Optional[Session]:
        """
        Get existing session without creating a new one

        Args:
            user_email: User's email address

        Returns:
            Session if exists and valid, None otherwise
        """
        async with self._lock:
            if user_email in self.sessions:
                session = self.sessions[user_email]
                if not session.is_expired(self.session_timeout):
                    session.update_access_time()
                    return session
                else:
                    # Session expired
                    await session.cleanup()
                    del self.sessions[user_email]
                    logger.info(f"Expired session removed for: {user_email}")

            return None

    async def invalidate_session(self, user_email: str):
        """
        Invalidate a user's session (e.g., on token expiry)

        Args:
            user_email: User's email address
        """
        async with self._lock:
            if user_email in self.sessions:
                session = self.sessions[user_email]
                session.invalidate_token()
                await session.cleanup()
                del self.sessions[user_email]
                logger.info(f"Session invalidated and removed for: {user_email}")

    async def _cleanup_expired_sessions(self):
        """
        Background task to clean up expired sessions periodically
        """
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval * 60)  # Convert minutes to seconds

                async with self._lock:
                    expired_users = []

                    for user_email, session in self.sessions.items():
                        if session.is_expired(self.session_timeout):
                            expired_users.append(user_email)

                    # Clean up expired sessions
                    for user_email in expired_users:
                        session = self.sessions[user_email]
                        await session.cleanup()
                        del self.sessions[user_email]
                        logger.info(f"Cleaned up expired session for: {user_email}")

                    if expired_users:
                        logger.info(f"Cleaned up {len(expired_users)} expired sessions")

                    # Log current session count
                    logger.debug(f"Active sessions: {len(self.sessions)}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about all active sessions

        Returns:
            Dictionary with session statistics
        """
        active_sessions = []
        for user_email, session in self.sessions.items():
            active_sessions.append({
                "user_email": user_email,
                "created_at": session.created_at.isoformat(),
                "last_accessed": session.last_accessed.isoformat(),
                "is_active": session.is_active,
                "initialized": session.initialized
            })

        return {
            "total_sessions": len(self.sessions),
            "session_timeout_minutes": self.session_timeout,
            "cleanup_interval_minutes": self.cleanup_interval,
            "sessions": active_sessions
        }


# Global SessionManager instance
session_manager = SessionManager(
    session_timeout_minutes=30,  # 30 minutes timeout
    cleanup_interval_minutes=5    # Cleanup every 5 minutes
)