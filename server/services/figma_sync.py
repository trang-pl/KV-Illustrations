"""
Figma Sync Service
Dịch vụ đồng bộ chính với Figma API
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
from config.settings import settings


class FigmaAPIClient:
    """Client để giao tiếp với Figma API"""

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"X-Figma-Token": token, "Content-Type": "application/json"}

    async def get_file_info(self, file_key: str) -> Optional[Dict]:
        """Lấy thông tin file-level bao gồm version"""
        url = f"{self.base_url}/files/{file_key}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 429:
                        print("⏱️ Rate limited - đang chờ...")
                        await asyncio.sleep(settings.figma.retry_delay)
                        return await self.get_file_info(file_key)
                    else:
                        print(f"❌ Lấy thông tin file thất bại: {response.status}")
                        return None
            except Exception as e:
                print(f"❌ Lỗi khi lấy thông tin file: {e}")
                return None

    async def get_node_structure(self, file_key: str, node_id: str) -> Optional[Dict]:
        """Lấy cấu trúc node chi tiết"""
        url = f"{self.base_url}/files/{file_key}/nodes"
        params = {"ids": node_id, "depth": 10}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "nodes" in data and node_id in data["nodes"]:
                            return data["nodes"][node_id]["document"]
                        return None
                    elif response.status == 429:
                        print("⏱️ Rate limited - đang chờ...")
                        await asyncio.sleep(settings.figma.retry_delay)
                        return await self.get_node_structure(file_key, node_id)
                    else:
                        print(f"❌ Lỗi API Node: {response.status}")
                        return None
            except Exception as e:
                print(f"❌ Lỗi khi lấy cấu trúc node: {e}")
                return None

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
                                print(f"❌ Không có hình ảnh trong response (lần thử {attempt + 1})")
                        elif response.status == 429:
                            print(f"⏱️ Rate limited - chờ {settings.figma.retry_delay}s...")
                            await asyncio.sleep(settings.figma.retry_delay)
                        else:
                            error_text = await response.text()
                            print(f"❌ Lỗi API Export: {response.status} - {error_text}")

                        if attempt < settings.figma.max_retries - 1:
                            await asyncio.sleep(2**attempt)

                except Exception as e:
                    print(f"❌ Lỗi trong export batch (lần thử {attempt + 1}): {e}")
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
                                print(f"❌ Nội dung SVG không hợp lệ (lần thử {attempt + 1})")
                        else:
                            print(f"❌ Tải SVG thất bại: {response.status}")

                        if attempt < settings.figma.max_retries - 1:
                            await asyncio.sleep(2**attempt)

            except Exception as e:
                print(f"❌ Lỗi tải SVG (lần thử {attempt + 1}): {e}")
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
    """Dịch vụ đồng bộ chính với Figma"""

    def __init__(self):
        self.api_client = FigmaAPIClient(settings.figma.api_token)
        self.change_detector = None
        self.dev_ready_detector = DevReadyDetector()

        # Thống kê
        self.stats = {"exported": 0, "failed": 0, "skipped": 0, "dev_ready": 0, "needs_review": 0}
        self.start_time = datetime.now()

    def setup_change_detection(self, cache_file: Path):
        """Thiết lập hệ thống phát hiện thay đổi"""
        self.change_detector = ChangeDetector(cache_file)

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
        naming_filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Xử lý quá trình đồng bộ chính"""
        print("🧠 Hệ thống Export SVG Figma nâng cao v2.0")
        print("=" * 60)
        print(f"📁 File: {file_key}")
        print(f"🎯 Root Node: {node_id}")
        print(f"📂 Output: {output_dir}")
        print(f"🔄 Force Sync: {force_sync}")
        print(f"⚙️ Batch Size: {settings.figma.batch_size}")
        print(f"⏱️ Delay: {settings.figma.delay_between_batches}s")
        print()

        # Thiết lập đường dẫn
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        cache_file = output_path / ".figma_cache.json"

        # Thiết lập phát hiện thay đổi
        if not self.change_detector:
            self.setup_change_detection(cache_file)

        # Bước 1: Lấy thông tin file
        print("📊 Bước 1: Đang lấy thông tin file...")
        file_info = await self.api_client.get_file_info(file_key)
        if not file_info:
            print("❌ Lấy thông tin file thất bại")
            return {"error": "Failed to get file information"}

        file_version = file_info.get("version", "unknown")
        print(f"📄 Phiên bản file: {file_version}")

        # Bước 2: Lấy cấu trúc node
        print("\n📊 Bước 2: Đang lấy cấu trúc node...")
        root_node = await self.api_client.get_node_structure(file_key, node_id)
        if not root_node:
            print("❌ Lấy cấu trúc node thất bại")
            return {"error": "Failed to get node structure"}

        print(f"✅ Root node: {root_node.get('name', 'Unknown')}")
        print(f"📦 Loại: {root_node.get('type')}")
        print(f"👶 Children: {len(root_node.get('children', []))}")

        # Bước 3: Tìm children có thể export
        print("\n🔍 Bước 3: Đang tìm children có thể export...")
        exportable_children = self.find_exportable_children(root_node)
        print(f"✅ Tìm thấy {len(exportable_children)} nodes có thể export")

        # Bước 4: Phát hiện thay đổi
        print("\n🔄 Bước 4: Đang phát hiện thay đổi...")
        nodes, change_stats = self.change_detector.detect_changes(exportable_children, file_version)

        print("📈 Thống kê thay đổi:")
        print(f"   🆕 Mới: {change_stats['new']}")
        print(f"   🔄 Đã sửa: {change_stats['modified']}")
        print(f"   ⚪ Không đổi: {change_stats['unchanged']}")
        print(f"   🗑️ Đã xóa: {change_stats['deleted']}")

        # Áp dụng naming filters
        if naming_filters:
            nodes = self.change_detector.apply_naming_filters(nodes, naming_filters)
            print(f"📝 Sau khi lọc: {len(nodes)} nodes")

        # Bước 5: Đánh giá dev-ready
        print("\n🚀 Bước 5: Đang đánh giá dev-ready...")
        for node in nodes:
            score, issues, status = self.dev_ready_detector.assess_readiness(node)
            node.dev_ready_score = score
            node.issues = issues
            node.status = status

        # Thống kê theo trạng thái
        status_counts = {}
        for node in nodes:
            status_counts[node.status.value] = status_counts.get(node.status.value, 0) + 1

        print("🎯 Thống kê dev-ready:")
        for status, count in status_counts.items():
            emoji = {
                "ready": "🟢",
                "approved": "🟢",
                "review": "🟡",
                "draft": "🟠",
                "unknown": "⚪",
            }.get(status, "⚪")
            print(f"   {emoji} {status.title()}: {count}")

        # Bước 6: Xử lý export
        nodes_to_export = nodes
        if not force_sync:
            nodes_to_export = [
                node
                for node in nodes
                if node.change_status in [ChangeStatus.NEW, ChangeStatus.MODIFIED]
            ]

        if not nodes_to_export:
            print("\n✅ Tất cả nodes đều đã cập nhật!")
            return {"message": "All nodes are up to date"}

        print(f"\n🚀 Bước 6: Đang export {len(nodes_to_export)} nodes...")

        # Xử lý theo batch
        batch_size = settings.figma.batch_size
        batches = [
            nodes_to_export[i : i + batch_size] for i in range(0, len(nodes_to_export), batch_size)
        ]

        print(f"📦 Xử lý {len(batches)} batches với tối đa {batch_size} nodes mỗi batch")

        for i, batch in enumerate(batches, 1):
            print(f"\n--- Batch {i}/{len(batches)} ---")
            await self._process_batch(file_key, batch, output_path, force_sync)

        # Bước 7: Lưu cache và tạo báo cáo
        print("\n💾 Bước 7: Đang lưu cache và tạo báo cáo...")
        self.change_detector._save_cache(nodes, file_version)

        # Tạo báo cáo toàn diện
        await self._generate_report(output_path, nodes, change_stats)

        # Tổng kết cuối cùng
        elapsed = datetime.now() - self.start_time
        print(f"\n📊 TỔNG KẾT EXPORT")
        print("=" * 50)
        print(f"✅ Đã export: {self.stats['exported']}")
        print(f"⏭️ Bỏ qua (không đổi): {self.stats['skipped']}")
        print(f"❌ Thất bại: {self.stats['failed']}")
        print(f"🟢 Dev-ready: {self.stats['dev_ready']}")
        print(f"🟡 Cần review: {self.stats['needs_review']}")
        print(f"⏱️ Thời gian tổng: {elapsed}")
        print(f"📁 Output: {output_path.absolute()}")

        if self.stats["exported"] > 0:
            print(f"\n🎉 Export hoàn thành! Kiểm tra {output_dir}/ để xem files")
        else:
            print(f"\n✅ Không cần export - mọi thứ đã cập nhật!")

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
            print(f"⏭️ Tất cả {len(nodes)} nodes không đổi, bỏ qua batch")
            return batch_stats

        print(
            f"\n🚀 Xử lý batch: {len(exportable_nodes)} nodes (bỏ qua {len(skipped_nodes)} không đổi)"
        )

        # Trích xuất node IDs để export
        node_ids = [node.id for node in exportable_nodes]

        # Lấy URLs SVG
        svg_urls = await self.api_client.export_svg_batch(file_key, node_ids)

        if not svg_urls:
            print(f"❌ Không nhận được SVG URLs")
            batch_stats["failed"] = len(exportable_nodes)
            return batch_stats

        print(f"✅ Nhận {len(svg_urls)} SVG URLs")

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
                print(f"❌ Không có SVG URL cho {node.name}")
                batch_stats["failed"] += 1
                self.stats["failed"] += 1

        # Rate limiting
        if settings.figma.delay_between_batches > 0:
            print(f"⏱️ Chờ {settings.figma.delay_between_batches}s...")
            await asyncio.sleep(settings.figma.delay_between_batches)

        return batch_stats

    async def _save_node_svg(self, node: NodeInfo, svg_url: str, output_dir: Path) -> bool:
        """Lưu SVG của node với metadata"""
        try:
            print(
                f"⬇️ Đang tải: {node.name} ({'🟢' if node.status.value == 'ready' else '🟡'})"
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

            # Emoji trạng thái
            status_emoji = (
                "🟢"
                if node.status.value == "ready"
                else "🟡"
                if node.status.value == "approved"
                else "🟠"
            )
            print(f"✅ Đã lưu: {filename} ({len(svg_content)} bytes) {status_emoji}")
            return True

        except Exception as e:
            print(f"❌ Lưu {node.name} thất bại: {e}")
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

        print(f"📋 Báo cáo chi tiết đã lưu: {report_file}")

        # Tạo tóm tắt dễ đọc
        summary_file = output_dir / "export_summary.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"# Tóm tắt Export\n\n")
            f.write(f"**Ngày:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Tổng quan\n")
            f.write(f"- Tổng nodes đã xử lý: {len(nodes)}\n")
            f.write(f"- Đã export thành công: {self.stats['exported']}\n")
            f.write(f"- Export thất bại: {self.stats['failed']}\n")
            f.write(f"- Icons dev-ready: {self.stats['dev_ready']}\n\n")

            f.write(f"## Thay đổi đã phát hiện\n")
            f.write(f"- Mới: {change_stats['new']}\n")
            f.write(f"- Đã sửa: {change_stats['modified']}\n")
            f.write(f"- Không đổi: {change_stats['unchanged']}\n")
            f.write(f"- Đã xóa: {change_stats['deleted']}\n\n")

            f.write(f"## Cấu hình\n")
            f.write(f"- Kích thước batch: {settings.figma.batch_size}\n")
            f.write(f"- Độ trễ giữa batches: {settings.figma.delay_between_batches}s\n")
            f.write(f"- Số lần retry tối đa: {settings.figma.max_retries}\n\n")

        print(f"📝 Báo cáo tóm tắt đã lưu: {summary_file}")