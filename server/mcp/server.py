"""
MCP Server Implementation
Triển khai MCP Server cho Figma Sync
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime

try:
    from mcp import NotificationOptions
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        LoggingLevel
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Define dummy types for when MCP is not available
    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text

    class Tool:
        def __init__(self, name: str, description: str, inputSchema: dict):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema

    logger = logging.getLogger(__name__)
    logger.warning("⚠️ MCP library not available. MCP server disabled.")


from ..services.figma_sync import FigmaSyncService
from ..workers.background_worker import BackgroundWorker
from config.settings import settings
from ..utils.helpers import generate_sync_id, validate_file_key, validate_node_id


logger = logging.getLogger(__name__)


class FigmaSyncMCPServer:
    """MCP Server cho Figma Sync operations"""

    def __init__(self):
        if not MCP_AVAILABLE:
            self.enabled = False
            return

        self.enabled = True
        self.sync_service = FigmaSyncService()
        self.background_worker = BackgroundWorker()

        # MCP Server setup
        self.server = Server("figma-sync-server")

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Liệt kê các tools có sẵn"""
            return [
                Tool(
                    name="sync_figma_assets",
                    description="Đồng bộ assets từ Figma file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_key": {
                                "type": "string",
                                "description": "Figma file key"
                            },
                            "node_id": {
                                "type": "string",
                                "description": "Root node ID để export"
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Thư mục output"
                            },
                            "force_sync": {
                                "type": "boolean",
                                "description": "Buộc đồng bộ tất cả",
                                "default": False
                            }
                        },
                        "required": ["file_key", "node_id", "output_dir"]
                    }
                ),
                Tool(
                    name="get_sync_status",
                    description="Lấy trạng thái đồng bộ",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sync_id": {
                                "type": "string",
                                "description": "ID của sync job"
                            }
                        },
                        "required": ["sync_id"]
                    }
                ),
                Tool(
                    name="list_sync_jobs",
                    description="Liệt kê các sync jobs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["running", "completed", "failed", "all"],
                                "description": "Lọc theo trạng thái",
                                "default": "all"
                            }
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Xử lý tool calls"""
            try:
                if name == "sync_figma_assets":
                    return await self._handle_sync_figma_assets(arguments)
                elif name == "get_sync_status":
                    return await self._handle_get_sync_status(arguments)
                elif name == "list_sync_jobs":
                    return await self._handle_list_sync_jobs(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"❌ Unknown tool: {name}"
                    )]
            except Exception as e:
                logger.error(f"❌ Tool execution failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"❌ Error: {str(e)}"
                )]

    async def _handle_sync_figma_assets(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Xử lý sync Figma assets"""
        file_key = arguments.get("file_key")
        node_id = arguments.get("node_id")
        output_dir = arguments.get("output_dir")
        force_sync = arguments.get("force_sync", False)

        # Validate inputs
        if not validate_file_key(file_key):
            return [TextContent(
                type="text",
                text="❌ Invalid Figma file key"
            )]

        if not validate_node_id(node_id):
            return [TextContent(
                type="text",
                text="❌ Invalid node ID"
            )]

        # Generate sync ID
        sync_id = generate_sync_id()

        # Start background sync
        asyncio.create_task(
            self.background_worker.process_sync_job(
                sync_id=sync_id,
                file_key=file_key,
                node_id=node_id,
                output_dir=output_dir,
                force_sync=force_sync
            )
        )

        return [TextContent(
            type="text",
            text=f"✅ Sync job started: {sync_id}\n"
                 f"📁 File: {file_key}\n"
                 f"🎯 Node: {node_id}\n"
                 f"📂 Output: {output_dir}\n"
                 f"🔄 Force: {force_sync}\n\n"
                 f"Use get_sync_status tool to check progress."
        )]

    async def _handle_get_sync_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Lấy trạng thái sync"""
        sync_id = arguments.get("sync_id")

        if not sync_id:
            return [TextContent(
                type="text",
                text="❌ Sync ID required"
            )]

        status_data = self.background_worker.get_sync_status(sync_id)

        if not status_data:
            return [TextContent(
                type="text",
                text=f"❌ Sync job not found: {sync_id}"
            )]

        # Format status response
        response_lines = [
            f"📊 Sync Status: {sync_id}",
            f"🔄 Status: {status_data.get('status', 'unknown')}",
            f"📁 File: {status_data.get('file_key', 'N/A')}",
            f"🎯 Node: {status_data.get('node_id', 'N/A')}",
            f"📂 Output: {status_data.get('output_dir', 'N/A')}",
            f"⏱️  Created: {status_data.get('created_at', 'N/A')}",
        ]

        if status_data.get("completed_at"):
            response_lines.append(f"✅ Completed: {status_data['completed_at']}")

        # Progress info
        progress = status_data.get("progress", {})
        if progress:
            response_lines.extend([
                f"",
                f"📈 Progress:",
                f"   📦 Total nodes: {progress.get('total_nodes', 0)}",
                f"   🔄 Processed: {progress.get('processed', 0)}",
                f"   ✅ Exported: {progress.get('exported', 0)}",
                f"   ❌ Failed: {progress.get('failed', 0)}"
            ])

        # Change stats
        change_stats = status_data.get("change_stats", {})
        if change_stats:
            response_lines.extend([
                f"",
                f"🔄 Changes:",
                f"   🆕 New: {change_stats.get('new', 0)}",
                f"   🔄 Modified: {change_stats.get('modified', 0)}",
                f"   ⚪ Unchanged: {change_stats.get('unchanged', 0)}",
                f"   🗑️ Deleted: {change_stats.get('deleted', 0)}"
            ])

        # Dev-ready stats
        dev_ready_stats = status_data.get("dev_ready_stats", {})
        if dev_ready_stats:
            response_lines.extend([
                f"",
                f"🎯 Dev-ready:",
                f"   🟢 Ready: {dev_ready_stats.get('ready', 0)}",
                f"   🟢 Approved: {dev_ready_stats.get('approved', 0)}",
                f"   🟡 Review: {dev_ready_stats.get('review', 0)}",
                f"   🟠 Draft: {dev_ready_stats.get('draft', 0)}"
            ])

        # Errors
        errors = status_data.get("errors", [])
        if errors:
            response_lines.extend([
                f"",
                f"❌ Errors:",
                *[f"   • {error}" for error in errors]
            ])

        return [TextContent(
            type="text",
            text="\n".join(response_lines)
        )]

    async def _handle_list_sync_jobs(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Liệt kê sync jobs"""
        status_filter = arguments.get("status", "all")

        all_jobs = self.background_worker.get_all_jobs()

        if status_filter != "all":
            filtered_jobs = {
                sync_id: job
                for sync_id, job in all_jobs.items()
                if job.get("status") == status_filter
            }
        else:
            filtered_jobs = all_jobs

        if not filtered_jobs:
            return [TextContent(
                type="text",
                text=f"📝 No sync jobs found (filter: {status_filter})"
            )]

        response_lines = [f"📋 Sync Jobs ({len(filtered_jobs)} found):", ""]

        for sync_id, job in filtered_jobs.items():
            status_emoji = {
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
                "queued": "⏳",
                "cancelled": "🚫"
            }.get(job.get("status"), "❓")

            response_lines.extend([
                f"{status_emoji} {sync_id}",
                f"   📁 {job.get('file_key', 'N/A')}",
                f"   🎯 {job.get('node_id', 'N/A')}",
                f"   ⏱️  {job.get('created_at', 'N/A')}",
                ""
            ])

        return [TextContent(
            type="text",
            text="\n".join(response_lines)
        )]

    async def start(self):
        """Khởi động MCP server"""
        if not self.enabled:
            logger.error("❌ MCP server not available")
            return

        try:
            await self.background_worker.start()

            # Run MCP server
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="figma-sync-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
        except Exception as e:
            logger.error(f"❌ MCP server failed: {e}")
        finally:
            await self.background_worker.stop()


# Global MCP server instance
mcp_server = FigmaSyncMCPServer()


async def main():
    """Main entry point cho MCP server"""
    await mcp_server.start()


if __name__ == "__main__":
    asyncio.run(main())