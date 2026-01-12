"""
Template for exposing an existing project to the MCP web editor via a service class.

Copy this into `mcp_{server_name}/{server_name}_service.py` and customize.
The `@mcp_service` decorator captures metadata for the registry and schema generation.

IMPORTANT: Always use class-based structure, not standalone functions.
"""
from typing import List, Optional, Dict, Any

from mcp_editor.mcp_service_registry.mcp_service_decorator import mcp_service

# Import your real implementation here
# from your_project.core import YourClient, YourRepository
# from your_project.models import YourModel


class DemoService:
    """
    Demo Service - MCP 도구의 진입점 역할을 하는 서비스 클래스

    모든 MCP 도구는 이 클래스의 메서드로 정의됩니다.
    의존성(DB 연결, API 클라이언트 등)은 생성자에서 초기화합니다.

    Attributes:
        _client: 외부 API 클라이언트 (예시)
        _cache: 내부 캐시 (예시)
    """

    def __init__(self):
        """
        서비스 초기화 - 의존성 주입 및 설정

        여기서 다음을 초기화합니다:
        - 외부 API 클라이언트
        - 데이터베이스 연결
        - 캐시 인스턴스
        - 설정값 로드
        """
        # self._client = YourClient()
        # self._repository = YourRepository()
        self._cache: Dict[str, Any] = {}

    @mcp_service(
        tool_name="list_entities",          # MCP tool name (LLM-visible)
        description="List domain entities with optional filters",
        server_name="demo",                 # -> mcp_demo folder name
        service_name="list_entities",       # underlying method name
        category="read",
        tags=["listing", "demo"],
    )
    def list_entities(self, status: Optional[str] = None, limit: int = 20) -> List[dict]:
        """
        도메인 엔티티 목록 조회

        Args:
            status: 필터링할 상태값 (optional)
            limit: 반환할 최대 개수 (default: 20)

        Returns:
            엔티티 딕셔너리 목록

        Example:
            >>> svc = DemoService()
            >>> svc.list_entities(status="active", limit=10)
            [{"id": 1, "name": "Entity1", "status": "active"}, ...]
        """
        # Replace with your actual implementation:
        # return self._repository.find_all(status=status, limit=limit)
        return []

    @mcp_service(
        tool_name="get_entity",
        description="Get a single entity by ID",
        server_name="demo",
        service_name="get_entity",
        category="read",
        tags=["get", "demo"],
    )
    def get_entity(self, entity_id: str) -> Optional[dict]:
        """
        단일 엔티티 조회

        Args:
            entity_id: 조회할 엔티티 ID

        Returns:
            엔티티 딕셔너리 또는 None
        """
        # return self._repository.find_by_id(entity_id)
        return None

    @mcp_service(
        tool_name="create_entity",
        description="Create a new domain entity from provided fields",
        server_name="demo",
        service_name="create_entity",
        category="write",
        tags=["create", "demo"],
    )
    def create_entity(
        self,
        name: str,
        owner: str,
        priority: Optional[int] = None
    ) -> dict:
        """
        새 엔티티 생성

        Args:
            name: 엔티티 이름 (required)
            owner: 소유자 (required)
            priority: 우선순위 (optional)

        Returns:
            생성된 엔티티 딕셔너리
        """
        # return self._repository.create(name=name, owner=owner, priority=priority)
        return {"name": name, "owner": owner, "priority": priority}

    @mcp_service(
        tool_name="update_entity",
        description="Update an existing entity",
        server_name="demo",
        service_name="update_entity",
        category="write",
        tags=["update", "demo"],
    )
    def update_entity(
        self,
        entity_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None
    ) -> dict:
        """
        기존 엔티티 수정

        Args:
            entity_id: 수정할 엔티티 ID (required)
            name: 새 이름 (optional)
            status: 새 상태 (optional)

        Returns:
            수정된 엔티티 딕셔너리
        """
        # return self._repository.update(entity_id, name=name, status=status)
        return {"id": entity_id, "name": name, "status": status}

    @mcp_service(
        tool_name="delete_entity",
        description="Delete an entity by ID",
        server_name="demo",
        service_name="delete_entity",
        category="write",
        tags=["delete", "demo"],
    )
    def delete_entity(self, entity_id: str) -> dict:
        """
        엔티티 삭제

        Args:
            entity_id: 삭제할 엔티티 ID

        Returns:
            삭제 결과 딕셔너리
        """
        # self._repository.delete(entity_id)
        return {"deleted": True, "id": entity_id}

    @mcp_service(
        tool_name="health_check",
        description="Check service health status",
        server_name="demo",
        service_name="health_check",
        category="system",
        tags=["health", "system"],
    )
    def health_check(self) -> dict:
        """
        서비스 상태 확인

        Returns:
            상태 정보 딕셔너리
        """
        return {
            "status": "healthy",
            "service": "demo",
            "cache_size": len(self._cache)
        }


# 서비스 인스턴스 생성 (스캐너가 메서드를 찾을 수 있도록)
# 웹 에디터 스캐너는 이 인스턴스의 @mcp_service 데코레이터된 메서드를 자동 감지합니다.
demo_service = DemoService()
