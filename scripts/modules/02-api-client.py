#!/usr/bin/env python3
"""
API Client Module v1.0
======================

Figma API client với async operations và rate limiting.
Handles file fetching, page processing, và node data retrieval.

Features:
- Async HTTP client với aiohttp
- Rate limiting và throttling
- Comprehensive error handling
- Unicode-safe operations
- Connection pooling

Author: Kilo Code Debug Agent
Version: 1.0.0
Date: 2025-08-29
"""

import asyncio
import aiohttp
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class PageData:
    """Represents a Figma page with its nodes"""
    id: str
    name: str
    node_count: int
    visible_nodes: List[Dict[str, Any]]

@dataclass
class NodeData:
    """Represents a Figma node"""
    id: str
    name: str
    type: str
    visible: bool
    data: Dict[str, Any]

class FigmaApiClient:
    """Async Figma API client với rate limiting và error handling"""

    def __init__(self, api_token: str, config_manager=None):
        """
        Initialize Figma API client

        Args:
            api_token: Figma API token
            config_manager: Config manager instance (optional)
        """
        self.api_token = api_token
        self.config_manager = config_manager
        self.session: Optional[aiohttp.ClientSession] = None

        # Load API settings from config
        if config_manager:
            api_settings = config_manager.get_api_settings()
            self.base_url = api_settings.base_url
            self.requests_per_minute = api_settings.requests_per_minute
            timeout_seconds = api_settings.timeout
        else:
            # Default values if no config manager
            self.base_url = "https://api.figma.com/v1"
            self.requests_per_minute = 60
            timeout_seconds = 30

        # Rate limiting settings
        self.request_interval = 60.0 / self.requests_per_minute
        self.last_request_time = 0

        # Headers
        self.headers = {
            "X-Figma-Token": api_token,
            "User-Agent": "Figma-Client-Module/1.0"
        }

        print(f"[DEBUG] [API_CLIENT] FigmaApiClient initialized with base_url: {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()

    async def initialize_session(self):
        """Initialize aiohttp session"""
        if self.session is None:
            # Use timeout from config or default
            timeout_seconds = self.config_manager.get_api_settings().timeout if self.config_manager else 30
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )
            print(f"[DEBUG] [API_CLIENT] HTTP session initialized with timeout: {timeout_seconds}s")

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
            print("[DEBUG] [API_CLIENT] HTTP session closed")

    async def _rate_limit_wait(self):
        """Implement rate limiting"""
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.request_interval:
            wait_time = self.request_interval - time_since_last_request
            print(f"[DEBUG] [API_CLIENT] Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

        self.last_request_time = asyncio.get_event_loop().time()

    async def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make HTTP request với error handling và rate limiting

        Args:
            url: Request URL
            params: Query parameters

        Returns:
            Response data or error dict
        """
        if not self.session:
            await self.initialize_session()

        await self._rate_limit_wait()

        try:
            print(f"[DEBUG] [API_CLIENT] Making request to: {url}")

            async with self.session.get(url, params=params) as response:
                response_time = asyncio.get_event_loop().time()

                if response.status == 200:
                    data = await response.json()
                    print(f"[DEBUG] [API_CLIENT] Request successful (status: {response.status})")
                    return {
                        "success": True,
                        "data": data,
                        "status_code": response.status,
                        "response_time": response_time
                    }
                else:
                    error_text = await response.text()
                    print(f"[DEBUG] [API_CLIENT] Request failed (status: {response.status})")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "status_code": response.status,
                        "response_time": response_time
                    }

        except asyncio.TimeoutError:
            error_msg = "Request timeout"
            print(f"[DEBUG] [API_CLIENT] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": None,
                "response_time": None
            }
        except aiohttp.ClientError as e:
            error_msg = f"Network error: {str(e)}"
            print(f"[DEBUG] [API_CLIENT] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": None,
                "response_time": None
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[DEBUG] [API_CLIENT] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": None,
                "response_time": None
            }

    async def fetch_file_data(self, file_key: str, include_pages: bool = True) -> Dict[str, Any]:
        """
        Fetch basic file data from Figma API

        Args:
            file_key: Figma file key
            include_pages: Whether to include page data

        Returns:
            File data response
        """
        print(f"[DEBUG] [API_CLIENT] Fetching file data for: {file_key}")

        url = f"{self.base_url}/files/{file_key}"
        params = {"depth": 1} if include_pages else {}

        result = await self._make_request(url, params)

        if result["success"]:
            file_data = result["data"]
            return {
                "success": True,
                "file_data": {
                    "key": file_key,
                    "name": file_data.get("name", "Unknown"),
                    "last_modified": file_data.get("lastModified"),
                    "thumbnail_url": file_data.get("thumbnailUrl"),
                    "version": file_data.get("version"),
                    "role": file_data.get("role")
                },
                "pages_count": len(file_data.get("document", {}).get("children", [])),
                "response_time": result.get("response_time")
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "file_key": file_key
            }

    async def fetch_file_pages(self, file_key: str) -> Dict[str, Any]:
        """
        Fetch detailed page data từ Figma API

        Args:
            file_key: Figma file key

        Returns:
            Pages data response
        """
        print(f"[DEBUG] [API_CLIENT] Fetching pages for file: {file_key}")

        url = f"{self.base_url}/files/{file_key}"
        params = {"depth": 3}  # Include nested children for complete data

        result = await self._make_request(url, params)

        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error"),
                "file_key": file_key
            }

        try:
            file_data = result["data"]
            document = file_data.get("document", {})
            pages = document.get("children", [])

            processed_pages = []
            total_nodes = 0

            for page in pages:
                page_id = page.get("id")
                page_name = page.get("name", "Unnamed Page")

                # Extract visible nodes from page
                visible_nodes = []
                if "children" in page:
                    for node in page["children"]:
                        if node.get("visible", True):  # Default to visible if not specified
                            visible_nodes.append({
                                "id": node.get("id"),
                                "name": node.get("name", "Unnamed Node"),
                                "type": node.get("type", "UNKNOWN"),
                                "visible": node.get("visible", True)
                            })

                page_data = PageData(
                    id=page_id,
                    name=page_name,
                    node_count=len(visible_nodes),
                    visible_nodes=visible_nodes
                )

                processed_pages.append({
                    "id": page_data.id,
                    "name": page_data.name,
                    "node_count": page_data.node_count,
                    "visible_nodes": page_data.visible_nodes
                })

                total_nodes += len(visible_nodes)

            return {
                "success": True,
                "file_key": file_key,
                "pages": processed_pages,
                "total_pages": len(processed_pages),
                "total_nodes": total_nodes,
                "response_time": result.get("response_time")
            }

        except Exception as e:
            error_msg = f"Error processing page data: {str(e)}"
            print(f"[DEBUG] [API_CLIENT] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "file_key": file_key
            }

    async def fetch_node_data(self, file_key: str, node_id: str) -> Dict[str, Any]:
        """
        Fetch detailed data for a specific node

        Args:
            file_key: Figma file key
            node_id: Node ID to fetch

        Returns:
            Node data response
        """
        print(f"[DEBUG] [API_CLIENT] Fetching node data: {node_id}")

        url = f"{self.base_url}/files/{file_key}/nodes"
        params = {"ids": node_id}

        result = await self._make_request(url, params)

        if result["success"]:
            nodes_data = result["data"].get("nodes", {})
            if node_id in nodes_data:
                node_data = nodes_data[node_id]
                document = node_data.get("document", {})

                return {
                    "success": True,
                    "node_id": node_id,
                    "data": {
                        "id": document.get("id"),
                        "name": document.get("name"),
                        "type": document.get("type"),
                        "visible": document.get("visible", True),
                        "absoluteBoundingBox": document.get("absoluteBoundingBox"),
                        "fills": document.get("fills", []),
                        "strokes": document.get("strokes", [])
                    },
                    "response_time": result.get("response_time")
                }
            else:
                return {
                    "success": False,
                    "error": f"Node {node_id} not found",
                    "node_id": node_id
                }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "node_id": node_id
            }

    async def test_connectivity(self, file_key: str) -> Dict[str, Any]:
        """
        Test API connectivity với basic file request

        Args:
            file_key: Figma file key for testing

        Returns:
            Connectivity test result
        """
        print("[DEBUG] [API_CLIENT] Testing API connectivity")

        result = await self.fetch_file_data(file_key, include_pages=False)

        return {
            "success": result["success"],
            "error": result.get("error"),
            "response_time": result.get("response_time"),
            "file_accessible": result["success"]
        }

# Export main class
__all__ = ['FigmaApiClient', 'PageData', 'NodeData']