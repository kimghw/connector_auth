#!/usr/bin/env python3
"""
MCP Project Creator
간편하게 새로운 MCP 서비스 프로젝트를 생성하는 도구
"""
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
import sys


class MCPProjectCreator:
    """MCP 프로젝트 생성기"""

    def __init__(self, base_dir: Optional[str] = None):
        """
        Args:
            base_dir: 프로젝트를 생성할 기본 디렉토리 (기본값: 상위 디렉토리)
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # jinja 폴더에서 실행 시 상위 디렉토리를 기본으로 사용
            current_dir = Path.cwd()
            if current_dir.name == "jinja":
                self.base_dir = current_dir.parent
            else:
                self.base_dir = current_dir

        self.templates_dir = self.base_dir / "templates" / "mcp_templates"

    def create_project(
        self,
        service_name: str,
        description: str = "",
        port: int = 8080,
        author: str = "",
        include_types: bool = True
    ) -> Dict[str, Any]:
        """
        새로운 MCP 프로젝트 생성

        Args:
            service_name: 서비스 이름 (예: "calendar", "weather")
            description: 서비스 설명
            port: 서버 포트 번호
            author: 작성자 이름
            include_types: 타입 정의 파일 포함 여부

        Returns:
            생성 결과 정보
        """
        print(f"\n🚀 Creating MCP Project: {service_name}")
        print("=" * 60)

        result = {
            "service_name": service_name,
            "created_files": [],
            "created_dirs": [],
            "errors": []
        }

        try:
            # 1. 메인 디렉토리 구조 생성
            project_dir = self.base_dir / f"mcp_{service_name}"
            mcp_server_dir = project_dir / "mcp_server"

            # 디렉토리 생성
            for directory in [project_dir, mcp_server_dir]:
                directory.mkdir(parents=True, exist_ok=True)
                result["created_dirs"].append(str(directory))
                print(f"✓ Created directory: {directory.relative_to(self.base_dir)}")

            # 2. __init__.py 파일 생성 (mcp_server)
            self._create_mcp_server_init(mcp_server_dir, service_name)
            result["created_files"].append(str(mcp_server_dir / "__init__.py"))

            # 3. server.py 생성
            self._create_server_py(mcp_server_dir, service_name, description, port)
            result["created_files"].append(str(mcp_server_dir / "server.py"))

            # 4. tool_definitions.py 생성
            self._create_tool_definitions(mcp_server_dir)
            result["created_files"].append(str(mcp_server_dir / "tool_definitions.py"))

            # 5. run.py 생성
            self._create_run_py(mcp_server_dir, port)
            result["created_files"].append(str(mcp_server_dir / "run.py"))

            # 6. 서비스 로직 파일 생성
            self._create_service_file(project_dir, service_name, description)
            result["created_files"].append(str(project_dir / f"{service_name}_service.py"))

            # 7. 타입 정의 파일 생성 (옵션)
            if include_types:
                self._create_types_file(project_dir, service_name)
                result["created_files"].append(str(project_dir / f"{service_name}_types.py"))

            # 8. __init__.py 파일 생성 (프로젝트 루트)
            self._create_project_init(project_dir, service_name, include_types)
            result["created_files"].append(str(project_dir / "__init__.py"))

            # 9. README.md 생성
            self._create_readme(project_dir, service_name, description, port, author)
            result["created_files"].append(str(project_dir / "README.md"))

            # 10. requirements.txt 생성
            self._create_requirements(project_dir)
            result["created_files"].append(str(project_dir / "requirements.txt"))

            # 11. .env.example 생성
            self._create_env_example(project_dir, service_name)
            result["created_files"].append(str(project_dir / ".env.example"))

            # 12. MCP 에디터 템플릿 파일 생성
            self._create_editor_template(service_name)
            print(f"✓ Created mcp_editor template file")

            # 13. generate_editor_config.py 실행하여 editor_config.json 업데이트
            self._run_generate_editor_config()
            print(f"✓ Updated mcp_editor/editor_config.json via generate_editor_config.py")

            print("\n" + "=" * 60)
            print(f"✅ Successfully created MCP project: {service_name}")
            print(f"\n📁 Project location: {project_dir.relative_to(self.base_dir)}")
            print("\n📋 Next steps:")
            print(f"  1. cd {project_dir.relative_to(self.base_dir)}")
            print(f"  2. python -m venv venv")
            print(f"  3. source venv/bin/activate  # Windows: venv\\Scripts\\activate")
            print(f"  4. pip install -r requirements.txt")
            print(f"  5. Implement your service logic in {service_name}_service.py")
            print(f"  6. Use MCP Web Editor to define tools:")
            print(f"     cd mcp_editor && python tool_editor_web.py")
            print(f"  7. Run server: cd mcp_server && python run.py")

        except Exception as e:
            error_msg = f"Error creating project: {str(e)}"
            result["errors"].append(error_msg)
            print(f"\n❌ {error_msg}")
            raise

        return result

    def _create_mcp_server_init(self, mcp_server_dir: Path, service_name: str):
        """mcp_server/__init__.py 생성"""
        content = f'''"""
MCP Server for {service_name.title()}
Provides Model Context Protocol interface for {service_name} operations
"""

from .server import app
from .tool_definitions import MCP_TOOLS

__all__ = ["app", "MCP_TOOLS"]
'''
        (mcp_server_dir / "__init__.py").write_text(content)
        print(f"✓ Created: mcp_server/__init__.py")

    def _create_server_py(self, mcp_server_dir: Path, service_name: str, description: str, port: int):
        """server.py 생성"""
        content = f'''"""
FastAPI MCP Server for {service_name.title()}
{description or f"MCP server implementation for {service_name} service"}
"""
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
import logging

# Add parent directories to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from tool_definitions import MCP_TOOLS
from {service_name}_service import {service_name.title()}Service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize service
service = {service_name.title()}Service()

# FastAPI app
app = FastAPI(
    title="{service_name.title()} MCP Server",
    description="{description or f'MCP server for {service_name} operations'}",
    version="1.0.0"
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {{
        "status": "healthy",
        "server": "{service_name}",
        "version": "1.0.0"
    }}

# MCP Protocol endpoints
@app.post("/mcp/v1/initialize")
async def initialize(request: Request):
    """Initialize MCP session"""
    body = await request.json()
    return {{
        "protocolVersion": "1.0",
        "serverInfo": {{
            "name": "{service_name}-mcp-server",
            "version": "1.0.0"
        }},
        "capabilities": {{
            "tools": {{}}
        }}
    }}

@app.post("/mcp/v1/tools/list")
async def list_tools(request: Request):
    """List available MCP tools"""
    return {{"tools": MCP_TOOLS}}

@app.post("/mcp/v1/tools/call")
async def call_tool(request: Request):
    """Execute MCP tool call"""
    try:
        body = await request.json()
        tool_name = body.get("name")
        arguments = body.get("arguments", {{}})

        logger.info(f"Tool call: {{tool_name}} with args: {{arguments}}")

        # Find tool definition
        tool_def = next((t for t in MCP_TOOLS if t["name"] == tool_name), None)
        if not tool_def:
            raise HTTPException(status_code=404, detail=f"Tool {{tool_name}} not found")

        # Route to service methods
        result = await route_tool_call(tool_name, arguments)

        return {{
            "content": [{{
                "type": "text",
                "text": json.dumps(result) if not isinstance(result, str) else result
            }}]
        }}

    except Exception as e:
        logger.error(f"Error in tool call: {{str(e)}}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def route_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Route tool calls to appropriate service methods"""

    # TODO: Implement routing logic based on your tool definitions
    # Example:
    # if tool_name == "example_tool":
    #     return await service.example_method(**arguments)

    # Default response for unimplemented tools
    return {{
        "status": "success",
        "message": f"Tool {{tool_name}} called with arguments {{arguments}}",
        "note": "Please implement the routing logic in route_tool_call()"
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port={port})
'''
        (mcp_server_dir / "server.py").write_text(content)
        print(f"✓ Created: mcp_server/server.py")

    def _create_tool_definitions(self, mcp_server_dir: Path):
        """tool_definitions.py 생성"""
        content = '''"""
MCP Tool Definitions
This file is managed by the MCP Web Editor
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [
    # Tools will be added via the MCP Web Editor
    # Example structure:
    # {
    #     "name": "example_tool",
    #     "description": "Example tool description",
    #     "inputSchema": {
    #         "type": "object",
    #         "properties": {
    #             "param1": {
    #                 "type": "string",
    #                 "description": "Parameter 1 description"
    #             }
    #         },
    #         "required": ["param1"]
    #     }
    # }
]
'''
        (mcp_server_dir / "tool_definitions.py").write_text(content)
        print(f"✓ Created: mcp_server/tool_definitions.py")

    def _create_run_py(self, mcp_server_dir: Path, port: int):
        """run.py 생성"""
        content = f'''#!/usr/bin/env python3
"""
Run script for MCP server
"""
import uvicorn
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port={port},
        reload=True,
        log_level="info"
    )
'''
        run_file = mcp_server_dir / "run.py"
        run_file.write_text(content)
        run_file.chmod(0o755)  # Make executable
        print(f"✓ Created: mcp_server/run.py")

    def _create_service_file(self, project_dir: Path, service_name: str, description: str):
        """서비스 로직 파일 생성"""
        content = f'''"""
{service_name.title()} Service Implementation
{description or f"Business logic for {service_name} operations"}
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class {service_name.title()}Service:
    """Main service class for {service_name} operations"""

    def __init__(self):
        """Initialize the service"""
        logger.info(f"Initializing {{self.__class__.__name__}}")
        # TODO: Initialize any required connections or resources

    async def example_method(self, param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
        """
        Example service method

        Args:
            param1: First parameter
            param2: Optional second parameter

        Returns:
            Result dictionary
        """
        logger.info(f"example_method called with param1={{param1}}, param2={{param2}}")

        # TODO: Implement your business logic here
        result = {{
            "status": "success",
            "param1": param1,
            "param2": param2,
            "timestamp": datetime.now().isoformat()
        }}

        return result

    async def list_items(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Example list method

        Args:
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            List of items
        """
        logger.info(f"list_items called with limit={{limit}}, offset={{offset}}")

        # TODO: Implement your list logic here
        items = []
        for i in range(offset, min(offset + limit, 100)):
            items.append({{
                "id": i,
                "name": f"Item {{i}}",
                "created_at": datetime.now().isoformat()
            }})

        return items

    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """
        Example get method

        Args:
            item_id: Item identifier

        Returns:
            Item details
        """
        logger.info(f"get_item called with item_id={{item_id}}")

        # TODO: Implement your get logic here
        return {{
            "id": item_id,
            "name": f"Item {{item_id}}",
            "description": "Example item",
            "created_at": datetime.now().isoformat()
        }}

    async def create_item(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Example create method

        Args:
            name: Item name
            description: Item description

        Returns:
            Created item
        """
        logger.info(f"create_item called with name={{name}}")

        # TODO: Implement your create logic here
        return {{
            "id": "generated_id",
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat()
        }}

    async def update_item(self, item_id: str, **kwargs) -> Dict[str, Any]:
        """
        Example update method

        Args:
            item_id: Item identifier
            **kwargs: Fields to update

        Returns:
            Updated item
        """
        logger.info(f"update_item called with item_id={{item_id}}, updates={{kwargs}}")

        # TODO: Implement your update logic here
        return {{
            "id": item_id,
            "updated_fields": list(kwargs.keys()),
            "updated_at": datetime.now().isoformat()
        }}

    async def delete_item(self, item_id: str) -> Dict[str, Any]:
        """
        Example delete method

        Args:
            item_id: Item identifier

        Returns:
            Deletion result
        """
        logger.info(f"delete_item called with item_id={{item_id}}")

        # TODO: Implement your delete logic here
        return {{
            "id": item_id,
            "deleted": True,
            "deleted_at": datetime.now().isoformat()
        }}


# Create a singleton instance
{service_name}_service = {service_name.title()}Service()
'''
        (project_dir / f"{service_name}_service.py").write_text(content)
        print(f"✓ Created: {service_name}_service.py")

    def _create_types_file(self, project_dir: Path, service_name: str):
        """타입 정의 파일 생성"""
        content = f'''"""
Type definitions for {service_name.title()} service
Pydantic models for request/response validation
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class Status(str, Enum):
    """Status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseItem(BaseModel):
    """Base model for items"""
    id: Optional[str] = Field(None, description="Item identifier")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    status: Status = Field(Status.ACTIVE, description="Item status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    class Config:
        use_enum_values = True
        json_encoders = {{
            datetime: lambda v: v.isoformat() if v else None
        }}


class CreateItemRequest(BaseModel):
    """Request model for creating an item"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = Field(None)


class UpdateItemRequest(BaseModel):
    """Request model for updating an item"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[Status] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)


class ItemResponse(BaseItem):
    """Response model for a single item"""
    metadata: Optional[Dict[str, Any]] = Field(None)


class ItemListResponse(BaseModel):
    """Response model for a list of items"""
    items: List[ItemResponse] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Number of items per page")
    offset: int = Field(..., description="Number of items skipped")

    class Config:
        schema_extra = {{
            "example": {{
                "items": [
                    {{
                        "id": "item_1",
                        "name": "Example Item",
                        "description": "This is an example",
                        "status": "active",
                        "created_at": "2024-01-01T00:00:00Z"
                    }}
                ],
                "total": 100,
                "limit": 10,
                "offset": 0
            }}
        }}


class OperationResult(BaseModel):
    """Generic operation result"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: Optional[str] = Field(None, description="Operation message")
    data: Optional[Dict[str, Any]] = Field(None, description="Operation data")
    errors: Optional[List[str]] = Field(None, description="Error messages if any")

    class Config:
        schema_extra = {{
            "example": {{
                "success": True,
                "message": "Operation completed successfully",
                "data": {{"id": "item_1", "status": "completed"}}
            }}
        }}


# Export all models
__all__ = [
    "Status",
    "BaseItem",
    "CreateItemRequest",
    "UpdateItemRequest",
    "ItemResponse",
    "ItemListResponse",
    "OperationResult"
]
'''
        (project_dir / f"{service_name}_types.py").write_text(content)
        print(f"✓ Created: {service_name}_types.py")

    def _create_project_init(self, project_dir: Path, service_name: str, include_types: bool):
        """프로젝트 루트 __init__.py 생성"""
        types_import = f"\nfrom .{service_name}_types import *" if include_types else ""

        content = f'''"""
MCP {service_name.title()} Service Module
"""

__version__ = "1.0.0"

from .{service_name}_service import {service_name.title()}Service, {service_name}_service{types_import}

__all__ = [
    "{service_name.title()}Service",
    "{service_name}_service"
]
'''
        (project_dir / "__init__.py").write_text(content)
        print(f"✓ Created: __init__.py")

    def _create_readme(self, project_dir: Path, service_name: str, description: str, port: int, author: str):
        """README.md 생성"""
        content = f'''# MCP {service_name.title()} Service

{description or f"MCP (Model Context Protocol) server implementation for {service_name} operations."}

## 📋 Overview

This is an MCP server that provides {service_name} functionality through a standardized protocol interface.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd mcp_{service_name}
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables (if needed):**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Server

```bash
cd mcp_server
python run.py
```

The server will start on `http://localhost:{port}`

## 🛠️ Development

### Project Structure

```
mcp_{service_name}/
├── mcp_server/          # MCP server implementation
│   ├── server.py        # FastAPI server
│   ├── tool_definitions.py  # MCP tool definitions
│   └── run.py          # Server runner script
├── {service_name}_service.py   # Business logic implementation
├── {service_name}_types.py     # Type definitions (Pydantic models)
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Adding Tools

1. Use the MCP Web Editor to define tools:
   ```bash
   cd ../mcp_editor
   python tool_editor_web.py
   ```

2. Select the `{service_name}` profile in the web interface

3. Define your tools and generate the server code

### Implementing Service Logic

Edit `{service_name}_service.py` to implement your business logic. The service class methods should correspond to the tools defined in the MCP Web Editor.

Example:
```python
async def your_method(self, param1: str, param2: int) -> Dict[str, Any]:
    # Your implementation here
    return {{"result": "success"}}
```

## 📡 API Endpoints

### Health Check
- `GET /health` - Server health status

### MCP Protocol
- `POST /mcp/v1/initialize` - Initialize MCP session
- `POST /mcp/v1/tools/list` - List available tools
- `POST /mcp/v1/tools/call` - Execute tool call

## 🧪 Testing

### Manual Testing

1. **Health check:**
   ```bash
   curl http://localhost:{port}/health
   ```

2. **List tools:**
   ```bash
   curl -X POST http://localhost:{port}/mcp/v1/tools/list \\
        -H "Content-Type: application/json"
   ```

3. **Call a tool:**
   ```bash
   curl -X POST http://localhost:{port}/mcp/v1/tools/call \\
        -H "Content-Type: application/json" \\
        -d '{{"name": "tool_name", "arguments": {{}}}}'
   ```

## 📝 Configuration

### Environment Variables

See `.env.example` for available configuration options.

### Port Configuration

Default port: `{port}`

To change the port, edit `mcp_server/run.py` or set the `PORT` environment variable.

## 🤝 Contributing

1. Implement new features in `{service_name}_service.py`
2. Define corresponding tools using the MCP Web Editor
3. Test your implementation
4. Document your changes

## 📄 License

[Your License Here]

## 👤 Author

{author or "Your Name"}

---
Generated with MCP Project Creator
'''
        (project_dir / "README.md").write_text(content)
        print(f"✓ Created: README.md")

    def _create_requirements(self, project_dir: Path):
        """requirements.txt 생성"""
        content = '''# Core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0

# HTTP client
httpx==0.25.2

# Logging
python-json-logger==2.0.7

# Optional: Add service-specific dependencies below
# azure-identity==1.15.0
# azure-mgmt-resource==23.0.1
# requests==2.31.0
# aiofiles==23.2.1
'''
        (project_dir / "requirements.txt").write_text(content)
        print(f"✓ Created: requirements.txt")

    def _create_env_example(self, project_dir: Path, service_name: str):
        """.env.example 생성"""
        content = f'''# {service_name.upper()} Service Configuration

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
LOG_LEVEL=INFO

# Service Configuration
# Add your service-specific environment variables here
# API_KEY=your_api_key_here
# API_URL=https://api.example.com
# DATABASE_URL=postgresql://user:pass@localhost/dbname

# Authentication (if needed)
# CLIENT_ID=your_client_id
# CLIENT_SECRET=your_client_secret
# TENANT_ID=your_tenant_id

# Feature Flags
# ENABLE_CACHE=true
# CACHE_TTL=3600
'''
        (project_dir / ".env.example").write_text(content)
        print(f"✓ Created: .env.example")

    def _run_generate_editor_config(self):
        """generate_editor_config.py 스크립트 실행"""
        generate_config_script = self.base_dir / "jinja" / "generate_editor_config.py"

        if not generate_config_script.exists():
            print(f"⚠️ Warning: {generate_config_script} not found, skipping editor config generation")
            return

        try:
            result = subprocess.run(
                [sys.executable, str(generate_config_script)],
                capture_output=True,
                text=True,
                cwd=str(self.base_dir)
            )

            if result.returncode != 0:
                print(f"⚠️ Warning: Error running generate_editor_config.py: {result.stderr}")
            else:
                # generate_editor_config.py의 출력 숨김 (이미 진행 상황을 표시 중)
                pass
        except Exception as e:
            print(f"⚠️ Warning: Failed to run generate_editor_config.py: {str(e)}")

    def _create_editor_template(self, service_name: str):
        """MCP 에디터 템플릿 파일 생성"""
        template_dir = self.base_dir / "mcp_editor" / f"mcp_{service_name}"
        template_dir.mkdir(parents=True, exist_ok=True)

        content = f'''"""
MCP Tool Definition Templates for {service_name.title()}
AUTO-GENERATED FILE - Edit via MCP Web Editor
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [
    # Tools will be added via the web editor
    # Use the MCP Web Editor to define and manage tools
]
'''
        (template_dir / "tool_definition_templates.py").write_text(content)


def main():
    """CLI 엔트리 포인트"""
    parser = argparse.ArgumentParser(
        description="Create a new MCP service project with standard structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s calendar --port 8090
  %(prog)s weather --description "Weather service for MCP" --author "John Doe"
  %(prog)s database --port 8100 --no-types
        """
    )

    parser.add_argument(
        "service_name",
        help="Name of the service (e.g., 'calendar', 'weather')"
    )
    parser.add_argument(
        "--description", "-d",
        default="",
        help="Service description"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Server port number (default: 8080)"
    )
    parser.add_argument(
        "--author", "-a",
        default="",
        help="Author name for documentation"
    )
    parser.add_argument(
        "--no-types",
        action="store_true",
        help="Don't create type definition file"
    )
    parser.add_argument(
        "--base-dir", "-b",
        default=None,
        help="Base directory for project creation (default: parent directory if run from jinja/)"
    )

    args = parser.parse_args()

    # 서비스 이름 검증
    if not args.service_name.replace("_", "").isalnum():
        print("❌ Error: Service name should only contain letters, numbers, and underscores")
        sys.exit(1)

    # 프로젝트 생성
    creator = MCPProjectCreator(args.base_dir)

    try:
        result = creator.create_project(
            service_name=args.service_name.lower(),
            description=args.description,
            port=args.port,
            author=args.author,
            include_types=not args.no_types
        )

        if result["errors"]:
            print("\n⚠️  Some errors occurred during creation:")
            for error in result["errors"]:
                print(f"  - {error}")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()