"""MCP server for attachment processing."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializeResult
from mcp.types import Tool, TextContent, CallToolResult

from ..file_manager import FileManager
from .tool_definitions import MCP_TOOLS, validate_tool_input

logger = logging.getLogger(__name__)


class MCPAttachmentServer:
    """MCP server for file attachment processing."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize MCP server.

        Args:
            config: Optional configuration
        """
        self.server = Server("mcp-attachment")
        self.file_manager = FileManager(config)
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            tools = []
            for tool_def in MCP_TOOLS:
                tools.append(Tool(
                    name=tool_def['name'],
                    description=tool_def['description'],
                    inputSchema=tool_def['inputSchema']
                ))
            return tools

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool calls."""
            try:
                # Validate input
                validation = validate_tool_input(name, arguments)
                if not validation['valid']:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"Validation error: {', '.join(validation['errors'])}"
                        )],
                        isError=True
                    )

                # Route to appropriate handler
                if name == "convert_file_to_text":
                    result = await self._handle_convert_file(arguments)
                elif name == "convert_onedrive_to_text":
                    result = await self._handle_convert_onedrive(arguments)
                elif name == "process_directory":
                    result = await self._handle_process_directory(arguments)
                elif name == "save_file_metadata":
                    result = await self._handle_save_metadata(arguments)
                elif name == "search_metadata":
                    result = await self._handle_search_metadata(arguments)
                elif name == "get_file_metadata":
                    result = await self._handle_get_metadata(arguments)
                elif name == "delete_file_metadata":
                    result = await self._handle_delete_metadata(arguments)
                else:
                    result = {
                        'success': False,
                        'error': f'Unknown tool: {name}'
                    }

                # Format response
                if result.get('success'):
                    content = result.get('text', json.dumps(result, indent=2))
                else:
                    content = f"Error: {result.get('error', 'Unknown error')}"

                return CallToolResult(
                    content=[TextContent(type="text", text=content)],
                    isError=not result.get('success', False)
                )

            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Execution error: {str(e)}"
                    )],
                    isError=True
                )

    async def _handle_convert_file(self, arguments: dict) -> Dict[str, Any]:
        """Handle file conversion.

        Args:
            arguments: Tool arguments

        Returns:
            Processing result
        """
        try:
            result = await asyncio.to_thread(
                self.file_manager.process,
                arguments['file_path'],
                **arguments
            )

            if arguments.get('output_format') == 'json':
                return {
                    'success': result['success'],
                    'data': result,
                    'text': json.dumps(result, indent=2)
                }
            else:
                return {
                    'success': result['success'],
                    'text': result.get('text', ''),
                    'error': ', '.join(result.get('errors', []))
                }

        except Exception as e:
            logger.error(f"File conversion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_convert_onedrive(self, arguments: dict) -> Dict[str, Any]:
        """Handle OneDrive conversion.

        Args:
            arguments: Tool arguments

        Returns:
            Processing result
        """
        try:
            result = await asyncio.to_thread(
                self.file_manager.process,
                arguments['url'],
                **arguments
            )

            if arguments.get('output_format') == 'json':
                return {
                    'success': result['success'],
                    'data': result,
                    'text': json.dumps(result, indent=2)
                }
            else:
                return {
                    'success': result['success'],
                    'text': result.get('text', ''),
                    'error': ', '.join(result.get('errors', []))
                }

        except Exception as e:
            logger.error(f"OneDrive conversion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_process_directory(self, arguments: dict) -> Dict[str, Any]:
        """Handle directory processing.

        Args:
            arguments: Tool arguments

        Returns:
            Processing result
        """
        try:
            results = await asyncio.to_thread(
                self.file_manager.process_directory,
                arguments['directory_path'],
                **arguments
            )

            summary = {
                'total': len(results),
                'successful': sum(1 for r in results if r['success']),
                'failed': sum(1 for r in results if not r['success']),
                'results': results
            }

            if arguments.get('output_format') == 'json':
                return {
                    'success': True,
                    'data': summary,
                    'text': json.dumps(summary, indent=2)
                }
            else:
                text_parts = [f"Processed {summary['total']} files"]
                text_parts.append(f"Success: {summary['successful']}")
                text_parts.append(f"Failed: {summary['failed']}")

                for result in results:
                    if result['success']:
                        text_parts.append(f"\n--- {result['file']} ---")
                        text_parts.append(result['text'][:500])  # First 500 chars

                return {
                    'success': True,
                    'text': '\n'.join(text_parts)
                }

        except Exception as e:
            logger.error(f"Directory processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_save_metadata(self, arguments: dict) -> Dict[str, Any]:
        """Handle metadata save.

        Args:
            arguments: Tool arguments

        Returns:
            Operation result
        """
        try:
            success = await asyncio.to_thread(
                self.file_manager.save_metadata,
                arguments['file_url'],
                arguments['keywords'],
                arguments.get('metadata')
            )

            return {
                'success': success,
                'text': 'Metadata saved successfully' if success else 'Failed to save metadata'
            }

        except Exception as e:
            logger.error(f"Metadata save failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_search_metadata(self, arguments: dict) -> Dict[str, Any]:
        """Handle metadata search.

        Args:
            arguments: Tool arguments

        Returns:
            Search results
        """
        try:
            results = await asyncio.to_thread(
                self.file_manager.search_metadata,
                **arguments
            )

            return {
                'success': True,
                'data': results,
                'text': json.dumps(results, indent=2)
            }

        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_get_metadata(self, arguments: dict) -> Dict[str, Any]:
        """Handle metadata retrieval.

        Args:
            arguments: Tool arguments

        Returns:
            Metadata or error
        """
        try:
            metadata = await asyncio.to_thread(
                self.file_manager.metadata_manager.get,
                arguments['file_url']
            )

            if metadata:
                return {
                    'success': True,
                    'data': metadata,
                    'text': json.dumps(metadata, indent=2)
                }
            else:
                return {
                    'success': False,
                    'error': 'Metadata not found'
                }

        except Exception as e:
            logger.error(f"Metadata retrieval failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_delete_metadata(self, arguments: dict) -> Dict[str, Any]:
        """Handle metadata deletion.

        Args:
            arguments: Tool arguments

        Returns:
            Operation result
        """
        try:
            success = await asyncio.to_thread(
                self.file_manager.metadata_manager.delete,
                arguments['file_url']
            )

            return {
                'success': success,
                'text': 'Metadata deleted successfully' if success else 'Failed to delete metadata'
            }

        except Exception as e:
            logger.error(f"Metadata deletion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def run(self):
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializeResult(
                    protocolVersion="2024-11-05",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    ),
                    serverInfo={
                        "name": "mcp-attachment",
                        "version": "1.0.0"
                    }
                )
            )


def main():
    """Main entry point for MCP server."""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s - %(message)s'
    )

    # Create and run server
    server = MCPAttachmentServer()

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()