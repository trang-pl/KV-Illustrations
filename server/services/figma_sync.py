"""
Figma Sync Service
Dịch vụ đồng bộ chính với Figma API
Improved với node ID conversion và enhanced fetch mechanism
"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .change_detector import ChangeDetector, NodeInfo, ChangeStatus
from .dev_ready_detector import DevReadyDetector
from ..utils.node_id_converter import NodeIdConverter, FigmaNodeResolver
from config.settings import settings


class FigmaAPIClient:
    """Client để giao tiếp với Figma API với improved fetch mechanism"""

    def __init__(self, token: str):
        if not token:
            raise ValueError("Figma API token is required and cannot be None")
        self.token = token
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"X-Figma-Token": token, "Content-Type": "application/json"}

        # Initialize node resolver for improved fetch
        self.node_resolver = FigmaNodeResolver(self)

    async def get_file_info(self, file_key: str) -> Optional[Dict]:
        """Lấy thông tin file-level bao gồm version"""
        url = f"{self.base_url}/files/{file_key}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            # Clean data to remove None keys that might cause serialization issues
                            data = self._clean_dict_keys(data)
                            return data
                        except Exception as json_error:
                            print(f"Loi parse JSON response: {json_error}")
                            # Print response text for debugging
                            response_text = await response.text()
                            print(f"Response text (first 500 chars): {response_text[:500]}")
                            return None
                    elif response.status == 429:
                        print("Rate limited - dang cho...")
                        await asyncio.sleep(settings.figma.retry_delay)
                        return await self.get_file_info(file_key)
                    else:
                        print(f"Lay thong tin file that bai: {response.status}")
                        # Print error response for debugging
                        try:
                            error_text = await response.text()
                            print(f"Error response: {error_text[:500]}")
                        except:
                            pass
                        return None
            except Exception as e:
                print(f"Loi khi lay thong tin file: {e}")
                import traceback
                traceback.print_exc()
                return None

    def _clean_dict_keys(self, data):
        """Clean dictionary to remove None keys and handle nested structures"""
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if key is not None:  # Skip None keys
                    cleaned[key] = self._clean_dict_keys(value)
            return cleaned
        elif isinstance(data, list):
            return [self._clean_dict_keys(item) for item in data]
        else:
            return data

    async def get_node_structure(self, file_key: str, node_id: str, depth: int = 10) -> Optional[Dict]:
        """Lấy cấu trúc node chi tiết với improved error handling"""
        url = f"{self.base_url}/files/{file_key}/nodes"
        params = {"ids": node_id, "depth": depth}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "nodes" in data and node_id in data["nodes"]:
                            return data["nodes"][node_id]["document"]
                        return None
                    elif response.status == 429:
                        print("Rate limited - dang cho...")
                        await asyncio.sleep(settings.figma.retry_delay)
                        return await self.get_node_structure(file_key, node_id)
                    else:
                        print(f"Loi API Node: {response.status}")
                        return None
            except Exception as e:
                print(f"Loi khi lay cau truc node: {e}")
                return None

    async def get_node_structure_with_fallback(self, file_key: str, node_id: str) -> Optional[Dict]:
        """Lấy cấu trúc node với fallback strategy"""
        return await self.node_resolver.resolve_node_with_fallbacks(file_key, node_id)

    async def smart_node_search(self, file_key: str, search_term: str, node_type: Optional[str] = None) -> List[Dict]:
        """Smart search cho nodes dựa trên tên"""
        return await self.node_resolver.smart_node_search(file_key, search_term, node_type)

    async def validate_node_access(self, file_key: str, node_ids: List[str]) -> Dict[str, bool]:
        """Validate access cho multiple nodes"""
        results = {}

        for node_id in node_ids:
            node_data = await self.get_node_structure(file_key, node_id)
            results[node_id] = node_data is not None

        return results

    async def get_node_with_enhanced_info(self, file_key: str, node_id: str) -> Optional[Dict]:
        """Lấy node với enhanced information và metadata"""
        # Try with fallback first
        resolved_result = await self.get_node_structure_with_fallback(file_key, node_id)

        if not resolved_result:
            return None

        node_data = resolved_result["node_data"]
        resolved_id = resolved_result["resolved_id"]

        # Add enhanced metadata
        enhanced_data = {
            **node_data,
            "_enhanced_metadata": {
                "original_node_id": node_id,
                "resolved_node_id": resolved_id,
                "format_used": resolved_result.get("format_used"),
                "fetch_timestamp": datetime.now().isoformat(),
                "node_id_validation": NodeIdConverter.validate_node_id(node_id),
                "coordinates": NodeIdConverter.extract_node_coordinates(resolved_id)
            }
        }

        return enhanced_data

    async def export_svg_batch(self, file_key: str, node_ids: List[str]) -> Dict[str, str]:
        """Export SVG theo batch với xử lý lỗi nâng cao"""
        if not node_ids:
            return {}

        url = f"{self.base_url}/images/{file_key}"
        params = {
            "ids": ",".join(node_ids),
            "format": "svg",
            "scale": 1,
            "svg_outline_text": "false",
            "svg_include_id": "true",
            "svg_simplify_stroke": "true",
        }

        for attempt in range(settings.figma.max_retries):
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, headers=self.headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            images = data.get("images", {})
                            if images:
                                return images
                            else:
                                print(f"Khong co hinh anh trong response (lan thu {attempt + 1})")
                        elif response.status == 429:
                            print(f"Rate limited - cho {settings.figma.retry_delay}s...")
                            await asyncio.sleep(settings.figma.retry_delay)
                        else:
                            error_text = await response.text()
                            print(f"Loi API Export: {response.status} - {error_text}")

                        if attempt < settings.figma.max_retries - 1:
                            await asyncio.sleep(2**attempt)

                except Exception as e:
                    print(f"Loi trong export batch (lan thu {attempt + 1}): {e}")
                    if attempt < settings.figma.max_retries - 1:
                        await asyncio.sleep(2**attempt)

        return {}

    async def download_svg_content(self, svg_url: str) -> Optional[str]:
        """Tải nội dung SVG với retry"""
        for attempt in range(settings.figma.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(svg_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            if content and content.strip().startswith("<"):
                                return content
                            else:
                                print(f"Noi dung SVG khong hop le (lan thu {attempt + 1})")
                        else:
                            print(f"Tai SVG that bai: {response.status}")

                        if attempt < settings.figma.max_retries - 1:
                            await asyncio.sleep(2**attempt)

            except Exception as e:
                print(f"Loi tai SVG (lan thu {attempt + 1}): {e}")
                if attempt < settings.figma.max_retries - 1:
                    await asyncio.sleep(2**attempt)

        return None

    def sanitize_filename(self, name: str) -> str:
        """Làm sạch tên file nâng cao"""
        # Loại bỏ/thay thế ký tự không hợp lệ
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")

        # Chuyển về lowercase và thay thế khoảng trắng bằng dấu gạch ngang
        name = name.lower().replace(" ", "-")

        # Loại bỏ dấu gạch ngang/gạch dưới liên tiếp
        name = re.sub(r"[-_]+", "-", name)

        # Loại bỏ dấu gạch ngang đầu và cuối
        name = name.strip("-_")

        # Giới hạn độ dài
        if len(name) > 100:
            name = name[:100].rstrip("-_")

        return name or "unnamed"


class FigmaSyncService:
    """Dịch vụ đồng bộ chính với Figma - Enhanced với Multi-Page Support"""

    def __init__(self):
        # Use environment variable directly to avoid settings loading issues
        import os
        token = os.environ.get('FIGMA_API_TOKEN')
        if not token:
            raise ValueError("FIGMA_API_TOKEN environment variable is not set. Please check your .env file.")
        self.api_client = FigmaAPIClient(token)
        self.change_detector = None
        self.dev_ready_detector = DevReadyDetector()

        # Thống kê
        self.stats = {"exported": 0, "failed": 0, "skipped": 0, "dev_ready": 0, "needs_review": 0}
        self.start_time = datetime.now()

    def setup_change_detection(self, cache_file: Path):
        """Thiết lập hệ thống phát hiện thay đổi"""
        self.change_detector = ChangeDetector(cache_file)

    async def get_file_pages(self, file_key: str) -> List[Dict]:
        """Lấy danh sách tất cả pages trong Figma file"""
        print("🔍 Đang lấy thông tin tất cả pages trong file...")

        file_info = await self.api_client.get_file_info(file_key)
        if not file_info:
            print("❌ Không thể lấy thông tin file")
            return []

        document = file_info.get("document", {})
        children = document.get("children", [])

        pages = []
        for child in children:
            if child.get("type") == "CANVAS":  # Pages are CANVAS type in Figma
                page_info = {
                    "id": child.get("id"),
                    "name": child.get("name", "Unnamed Page"),
                    "type": child.get("type"),
                    "backgroundColor": child.get("backgroundColor"),
                    "children_count": len(child.get("children", []))
                }
                pages.append(page_info)
                print(f"📄 Page: {page_info['name']} (ID: {page_info['id']}) - {page_info['children_count']} children")

        print(f"✅ Tìm thấy {len(pages)} pages trong file")
        return pages

    def find_exportable_children(self, node: Dict, max_depth: int = 5) -> List[Dict]:
        """Tìm tất cả children có thể export với metadata nâng cao"""
        exportable_children = []

        def traverse(current_node, depth=0, path=""):
            if depth > max_depth:
                return

            node_type = current_node.get("type", "")
            node_name = current_node.get("name", "Unnamed")
            node_id = current_node.get("id", "")

            current_path = f"{path}/{node_name}" if path else node_name

            # Kiểm tra loại exportable nâng cao
            exportable_types = ["COMPONENT", "INSTANCE", "FRAME", "GROUP"]
            if node_type in exportable_types and node_id:
                bbox = current_node.get("absoluteBoundingBox", {})
                width = bbox.get("width", 0)
                height = bbox.get("height", 0)

                if width > 0 and height > 0 and width <= 2000 and height <= 2000:
                    exportable_children.append(
                        {
                            "id": node_id,
                            "name": node_name,
                            "type": node_type,
                            "path": current_path,
                            "width": width,
                            "height": height,
                            "depth": depth,
                            "lastModified": current_node.get("lastModified"),
                            "version": current_node.get("version", 0),
                            "has_children": len(current_node.get("children", [])) > 0,
                            "fills": current_node.get("fills", []),
                            "effects": current_node.get("effects", []),
                        }
                    )

            # Duyệt children
            for child in current_node.get("children", []):
                traverse(child, depth + 1, current_path)

        traverse(node)
        return exportable_children

    async def process_sync(
        self,
        file_key: str,
        node_id: str,
        output_dir: str,
        force_sync: bool = False,
        naming_filters: Optional[Dict] = None,
        multi_page: bool = False
    ) -> Dict[str, Any]:
        """Xử lý quá trình đồng bộ chính - Enhanced với Multi-Page Support"""
        print("🚀 He thong Export SVG Figma nang cao v2.1 - Multi-Page Edition")
        print("=" * 70)
        print(f"File: {file_key}")
        print(f"Root Node: {node_id}")
        print(f"Output: {output_dir}")
        print(f"Force Sync: {force_sync}")
        print(f"Multi-Page Mode: {multi_page}")
        print(f"Batch Size: {settings.figma.batch_size}")
        print(f"Delay: {settings.figma.delay_between_batches}s")
        print()

        # Thiết lập đường dẫn
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        cache_file = output_path / ".figma_cache.json"

        # Thiết lập phát hiện thay đổi
        if not self.change_detector:
            self.setup_change_detection(cache_file)

        # Buoc 1: Lay thong tin file
        print("Buoc 1: Dang lay thong tin file...")
        file_info = await self.api_client.get_file_info(file_key)
        if not file_info:
            print("Lay thong tin file that bai")
            return {"error": "Failed to get file information"}

        file_version = file_info.get("version", "unknown")
        print(f"Phien ban file: {file_version}")

        # Buoc 2: Lay cau truc node(s) voi enhanced fetch mechanism
        print("\nBuoc 2: Dang lay cau truc node voi enhanced fetch...")

        if multi_page:
            # Multi-page mode: Get all pages and process each one
            print("🔄 Multi-Page Mode: Processing all pages in file...")
            pages = await self.get_file_pages(file_key)

            if not pages:
                print("❌ Không tìm thấy pages nào trong file")
                return {"error": "No pages found in file"}

            all_exportable_children = []
            page_results = []

            for page in pages:
                page_id = page["id"]
                page_name = page["name"]
                print(f"\n📄 Processing Page: {page_name} (ID: {page_id})")

                # Fetch node structure for this page
                resolved_result = await self.api_client.get_node_structure_with_fallback(file_key, page_id)

                if not resolved_result:
                    print(f"⚠️  Skipping page {page_name} - failed to get structure")
                    continue

                page_node = resolved_result["node_data"]
                actual_page_id = resolved_result["resolved_id"]

                print(f"   ✅ Page loaded: {page_node.get('name', 'Unknown')}")
                print(f"   📊 Children: {len(page_node.get('children', []))}")

                # Find exportable children in this page
                page_exportable = self.find_exportable_children(page_node)

                # Add page context to each child
                for child in page_exportable:
                    child["_page_context"] = {
                        "page_id": page_id,
                        "page_name": page_name,
                        "page_node_id": actual_page_id
                    }

                all_exportable_children.extend(page_exportable)
                page_results.append({
                    "page_id": page_id,
                    "page_name": page_name,
                    "exportable_count": len(page_exportable),
                    "total_children": len(page_node.get('children', []))
                })

                print(f"   🎯 Exportable nodes: {len(page_exportable)}")

            print(f"\n📈 Multi-Page Summary:")
            print(f"   Total pages processed: {len(page_results)}")
            print(f"   Total exportable nodes: {len(all_exportable_children)}")

            # For multi-page, we skip the normal find_exportable_children step
            # and use the already collected exportable children directly
            exportable_children = all_exportable_children
            actual_node_id = "multi-page-container"
            format_used = "multi-page"

            # Set root_node for compatibility with rest of the code
            root_node = {
                "name": "Multi-Page Container",
                "type": "MULTI_PAGE_CONTAINER",
                "children": all_exportable_children
            }

        else:
            # Single-page mode (original logic)
            print("🔸 Single-Page Mode: Processing single node...")
            resolved_result = await self.api_client.get_node_structure_with_fallback(file_key, node_id)

            if not resolved_result:
                print("Lay cau truc node that bai - tried all fallback formats")
                return {"error": "Failed to get node structure with any format"}

            root_node = resolved_result["node_data"]
            actual_node_id = resolved_result["resolved_id"]
            format_used = resolved_result.get("format_used", "unknown")

        print(f"Root node: {root_node.get('name', 'Unknown')}")
        print(f"Loai: {root_node.get('type')}")
        print(f"Children: {len(root_node.get('children', []))}")
        print(f"Resolved ID: {actual_node_id} (format: {format_used})")
        print(f"Original ID: {node_id}")

        # Buoc 3: Tim children co the export
        if multi_page:
            print("\nBuoc 3: Skipping find children (already collected in multi-page mode)...")
            print(f"Using {len(exportable_children)} pre-collected nodes from all pages")
        else:
            print("\nBuoc 3: Dang tim children co the export...")
            exportable_children = self.find_exportable_children(root_node)
            print(f"Tim thay {len(exportable_children)} nodes co the export")

        # Buoc 4: Phat hien thay doi
        print("\nBuoc 4: Dang phat hien thay doi...")
        nodes, change_stats = self.change_detector.detect_changes(exportable_children, file_version)

        print("Thong ke thay doi:")
        print(f"   Moi: {change_stats['new']}")
        print(f"   Da sua: {change_stats['modified']}")
        print(f"   Khong doi: {change_stats['unchanged']}")
        print(f"   Da xoa: {change_stats['deleted']}")

        # Ap dung naming filters
        if naming_filters:
            nodes = self.change_detector.apply_naming_filters(nodes, naming_filters)
            print(f"Sau khi loc: {len(nodes)} nodes")

        # Buoc 5: Danh gia dev-ready
        print("\nBuoc 5: Dang danh gia dev-ready...")
        for node in nodes:
            score, issues, status = self.dev_ready_detector.assess_readiness(node)
            node.dev_ready_score = score
            node.issues = issues
            node.status = status

        # Thống kê theo trạng thái
        status_counts = {}
        for node in nodes:
            status_counts[node.status.value] = status_counts.get(node.status.value, 0) + 1

        print("Thong ke dev-ready:")
        for status, count in status_counts.items():
            print(f"   {status.title()}: {count}")

        # Buoc 6: Xu ly export
        nodes_to_export = nodes
        if not force_sync:
            nodes_to_export = [
                node
                for node in nodes
                if node.change_status in [ChangeStatus.NEW, ChangeStatus.MODIFIED]
            ]

        if not nodes_to_export:
            print("\nTat ca nodes deu da cap nhat!")
            return {"message": "All nodes are up to date"}

        print(f"\nBuoc 6: Dang export {len(nodes_to_export)} nodes...")

        # Xử lý theo batch
        batch_size = settings.figma.batch_size
        batches = [
            nodes_to_export[i : i + batch_size] for i in range(0, len(nodes_to_export), batch_size)
        ]

        print(f"Xu ly {len(batches)} batches voi toi da {batch_size} nodes moi batch")

        for i, batch in enumerate(batches, 1):
            print(f"\n--- Batch {i}/{len(batches)} ---")
            await self._process_batch(file_key, batch, output_path, force_sync)

        # Buoc 7: Luu cache va tao bao cao
        print("\nBuoc 7: Dang luu cache va tao bao cao...")
        self.change_detector._save_cache(nodes, file_version)

        # Tao bao cao toan dien
        await self._generate_report(output_path, nodes, change_stats)

        # Tong ket cuoi cung
        elapsed = datetime.now() - self.start_time
        print(f"\nTONG KET EXPORT")
        print("=" * 50)
        print(f"Da export: {self.stats['exported']}")
        print(f"Bo qua (khong doi): {self.stats['skipped']}")
        print(f"That bai: {self.stats['failed']}")
        print(f"Dev-ready: {self.stats['dev_ready']}")
        print(f"Can review: {self.stats['needs_review']}")
        print(f"Thoi gian tong: {elapsed}")
        print(f"Output: {output_path.absolute()}")

        if self.stats["exported"] > 0:
            print(f"\nExport hoan thanh! Kiem tra {output_dir}/ de xem files")
        else:
            print(f"\nKhong can export - moi thu da cap nhat!")

        return {
            "exported": self.stats["exported"],
            "failed": self.stats["failed"],
            "skipped": self.stats["skipped"],
            "dev_ready": self.stats["dev_ready"],
            "needs_review": self.stats["needs_review"],
            "change_stats": change_stats,
            "status_counts": status_counts,
            "elapsed_time": str(elapsed)
        }

    async def _process_batch(
        self,
        file_key: str,
        nodes: List[NodeInfo],
        output_dir: Path,
        force_export: bool = False
    ) -> Dict[str, Any]:
        """Xử lý một batch nodes"""
        if not nodes:
            return {"exported": 0, "skipped": 0, "failed": 0}

        # Lọc nodes dựa trên trạng thái thay đổi và force_export
        if not force_export:
            exportable_nodes = [
                node
                for node in nodes
                if node.change_status in [ChangeStatus.NEW, ChangeStatus.MODIFIED]
            ]
            skipped_nodes = [node for node in nodes if node.change_status == ChangeStatus.UNCHANGED]
        else:
            exportable_nodes = nodes
            skipped_nodes = []

        batch_stats = {"exported": 0, "skipped": len(skipped_nodes), "failed": 0}

        if not exportable_nodes:
            print(f"Tat ca {len(nodes)} nodes khong doi, bo qua batch")
            return batch_stats

        print(
            f"\nXu ly batch: {len(exportable_nodes)} nodes (bo qua {len(skipped_nodes)} khong doi)"
        )

        # Trích xuất node IDs để export
        node_ids = [node.id for node in exportable_nodes]

        # Lấy URLs SVG
        svg_urls = await self.api_client.export_svg_batch(file_key, node_ids)

        if not svg_urls:
            print(f"Khong nhan duoc SVG URLs")
            batch_stats["failed"] = len(exportable_nodes)
            return batch_stats

        print(f"Nhan {len(svg_urls)} SVG URLs")

        # Tải và lưu từng SVG
        for node in exportable_nodes:
            if node.id in svg_urls:
                success = await self._save_node_svg(node, svg_urls[node.id], output_dir)
                if success:
                    batch_stats["exported"] += 1
                    self.stats["exported"] += 1

                    # Cập nhật thống kê dev-ready
                    if node.status.value == "ready":
                        self.stats["dev_ready"] += 1
                    elif node.status.value in ["review", "draft"]:
                        self.stats["needs_review"] += 1
                else:
                    batch_stats["failed"] += 1
                    self.stats["failed"] += 1
            else:
                print(f"Khong co SVG URL cho {node.name}")
                batch_stats["failed"] += 1
                self.stats["failed"] += 1

        # Rate limiting
        if settings.figma.delay_between_batches > 0:
            print(f"Cho {settings.figma.delay_between_batches}s...")
            await asyncio.sleep(settings.figma.delay_between_batches)

        return batch_stats

    async def _save_node_svg(self, node: NodeInfo, svg_url: str, output_dir: Path) -> bool:
        """Lưu SVG của node với metadata"""
        try:
            print(
                f"Dang tai: {node.name} ({'ready' if node.status.value == 'ready' else 'review'})"
            )

            # Tải nội dung SVG
            svg_content = await self.api_client.download_svg_content(svg_url)
            if not svg_content:
                return False

            # Tạo tên file với prefix trạng thái
            safe_name = self.api_client.sanitize_filename(node.name)
            status_prefix = ""
            if node.status.value == "ready":
                status_prefix = "ready_"
            elif node.status.value == "approved":
                status_prefix = "approved_"

            filename = f"{status_prefix}{safe_name}_{node.id.replace(':', '_')}.svg"
            filepath = output_dir / filename

            # Lưu file SVG
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(svg_content)

            # Cập nhật thông tin node
            node.exported_at = datetime.now().isoformat()
            node.svg_size = len(svg_content)

            # Lưu metadata chi tiết
            metadata = {
                **asdict(node),
                "config_used": {
                    "batch_size": settings.figma.batch_size,
                    "delay_between_batches": settings.figma.delay_between_batches,
                    "max_concurrent_requests": settings.figma.max_concurrent_requests,
                },
                "export_settings": {
                    "scale": 1,
                    "format": "svg",
                    "svg_outline_text": False,
                    "svg_include_id": True,
                    "svg_simplify_stroke": True,
                },
            }

            # Chuyển enum thành string để JSON serialization
            metadata["status"] = node.status.value
            metadata["change_status"] = node.change_status.value

            metadata_file = filepath.with_suffix(".json")
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # Trang thai
            status_text = (
                "ready"
                if node.status.value == "ready"
                else "approved"
                if node.status.value == "approved"
                else "draft"
            )
            print(f"Da luu: {filename} ({len(svg_content)} bytes) {status_text}")
            return True

        except Exception as e:
            print(f"Luu {node.name} that bai: {e}")
            return False

    async def _generate_report(
        self, output_dir: Path, nodes: List[NodeInfo], change_stats: Dict[str, int]
    ):
        """Tạo báo cáo toàn diện"""
        report_data = {
            "export_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_nodes": len(nodes),
                "change_stats": change_stats,
                "export_stats": self.stats.copy(),
                "config": {
                    "batch_size": settings.figma.batch_size,
                    "delay_between_batches": settings.figma.delay_between_batches,
                    "max_retries": settings.figma.max_retries,
                },
                "elapsed_time": str(datetime.now() - self.start_time),
            },
            "nodes": [],
        }

        # Thêm chi tiết node
        for node in nodes:
            node_data = asdict(node)
            node_data["status"] = node.status.value
            node_data["change_status"] = node.change_status.value
            report_data["nodes"].append(node_data)

        # Lưu báo cáo chi tiết
        report_file = output_dir / "export_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"Bao cao chi tiet da luu: {report_file}")

        # Tao tom tat de doc
        summary_file = output_dir / "export_summary.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"# Tom tat Export\n\n")
            f.write(f"**Ngay:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Tong quan\n")
            f.write(f"- Tong nodes da xu ly: {len(nodes)}\n")
            f.write(f"- Da export thanh cong: {self.stats['exported']}\n")
            f.write(f"- Export that bai: {self.stats['failed']}\n")
            f.write(f"- Icons dev-ready: {self.stats['dev_ready']}\n\n")

            f.write(f"## Thay doi da phat hien\n")
            f.write(f"- Moi: {change_stats['new']}\n")
            f.write(f"- Da sua: {change_stats['modified']}\n")
            f.write(f"- Khong doi: {change_stats['unchanged']}\n")
            f.write(f"- Da xoa: {change_stats['deleted']}\n\n")

            f.write(f"## Cau hinh\n")
            f.write(f"- Kich thuoc batch: {settings.figma.batch_size}\n")
            f.write(f"- Do tre giua batches: {settings.figma.delay_between_batches}s\n")
            f.write(f"- So lan retry toi da: {settings.figma.max_retries}\n\n")

        print(f"Bao cao tom tat da luu: {summary_file}")