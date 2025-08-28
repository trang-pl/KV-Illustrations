"""
Dev Ready Detector Service
Đánh giá mức độ sẵn sàng phát triển của nodes
"""

import re
from typing import List, Tuple
from .change_detector import NodeInfo, NodeStatus


class DevReadyDetector:
    """Đánh giá mức độ sẵn sàng phát triển của nodes"""

    def __init__(self):
        self.naming_pattern = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")  # kebab-case
        self.standard_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)]
        self.wip_keywords = ["wip", "draft", "temp", "test", "placeholder"]
        self.approved_keywords = ["approved", "ready", "final", "production"]

    def assess_readiness(self, node: NodeInfo) -> Tuple[float, List[str], NodeStatus]:
        """Đánh giá toàn diện mức độ dev-ready"""
        score = 0.0
        max_score = 100.0
        issues = []

        # 1. Quy tắc đặt tên (25 điểm)
        if self._check_naming_convention(node.name):
            score += 25
        else:
            issues.append(f"Đặt tên: '{node.name}' nên dùng kebab-case (vd: 'user-profile')")

        # 2. Kích thước chuẩn (20 điểm)
        size_score, size_issues = self._check_size_standards(node.width, node.height)
        score += size_score
        issues.extend(size_issues)

        # 3. Trạng thái hoàn thành (20 điểm)
        completion_score, completion_issues = self._check_completion_status(node.name, node.type)
        score += completion_score
        issues.extend(completion_issues)

        # 4. Sẵn sàng export (20 điểm)
        export_score, export_issues = self._check_export_readiness(
            node.width, node.height, node.type
        )
        score += export_score
        issues.extend(export_issues)

        # 5. Chất lượng ngữ nghĩa (15 điểm)
        semantic_score, semantic_issues = self._check_semantic_quality(node.name)
        score += semantic_score
        issues.extend(semantic_issues)

        # Xác định trạng thái
        status = self._determine_status(node.name, score / max_score)

        return score / max_score, issues, status

    def _check_naming_convention(self, name: str) -> bool:
        """Kiểm tra tên có theo quy tắc kebab-case không"""
        return self.naming_pattern.match(name.lower()) is not None

    def _check_size_standards(self, width: float, height: float) -> Tuple[float, List[str]]:
        """Kiểm tra kích thước có theo chuẩn icon không"""
        issues = []
        score = 0.0

        # Kiểm tra có phải hình vuông không
        if abs(width - height) < 1:  # Cho phép sai số 1px
            score += 10
        else:
            issues.append(f"Kích thước: Icon nên là hình vuông, nhận {width}x{height}")

        # Kiểm tra có phải kích thước chuẩn không
        is_standard = any(
            abs(width - sw) < 2 and abs(height - sh) < 2 for sw, sh in self.standard_sizes
        )

        if is_standard:
            score += 10
        else:
            standard_sizes_str = ", ".join(f"{w}x{h}" for w, h in self.standard_sizes)
            issues.append(
                f"Kích thước: Kích thước không chuẩn {width}x{height}. Đề xuất: {standard_sizes_str}"
            )

        return score, issues

    def _check_completion_status(self, name: str, node_type: str) -> Tuple[float, List[str]]:
        """Kiểm tra node có vẻ hoàn thành không"""
        issues = []
        score = 20.0  # Mặc định là hoàn thành

        name_lower = name.lower()

        # Kiểm tra từ khóa WIP
        if any(keyword in name_lower for keyword in self.wip_keywords):
            score = 5.0
            issues.append(f"Trạng thái: Chứa từ khóa WIP trong '{name}'")

        # Kiểm tra pattern placeholder
        if "untitled" in name_lower or name.startswith("Frame ") or name.startswith("Group "):
            score = 0.0
            issues.append(f"Trạng thái: Có vẻ là placeholder: '{name}'")

        return score, issues

    def _check_export_readiness(
        self, width: float, height: float, node_type: str
    ) -> Tuple[float, List[str]]:
        """Kiểm tra node có sẵn sàng export SVG không"""
        issues = []
        score = 20.0  # Mặc định là sẵn sàng

        # Kiểm tra giới hạn kích thước
        if width <= 0 or height <= 0:
            score = 0.0
            issues.append("Export: Kích thước không hợp lệ để export")
        elif width > 1000 or height > 1000:
            score = 10.0
            issues.append(f"Export: Kích thước lớn {width}x{height} có thể gây vấn đề")

        # Kiểm tra loại node
        exportable_types = ["COMPONENT", "INSTANCE", "FRAME", "GROUP"]
        if node_type not in exportable_types:
            score = 0.0
            issues.append(f"Export: Loại '{node_type}' có thể không export tốt")

        return score, issues

    def _check_semantic_quality(self, name: str) -> Tuple[float, List[str]]:
        """Kiểm tra chất lượng ngữ nghĩa của tên"""
        issues = []
        score = 15.0  # Mặc định là tốt

        # Kiểm tra độ dài
        if len(name) < 2:
            score = 0.0
            issues.append("Ngữ nghĩa: Tên quá ngắn")
        elif len(name) > 50:
            score = 5.0
            issues.append("Ngữ nghĩa: Tên quá dài, nên rút ngắn")

        # Kiểm tra số ở đầu tên
        if name and name[0].isdigit():
            score *= 0.5
            issues.append("Ngữ nghĩa: Tránh bắt đầu tên bằng số")

        return score, issues

    def _determine_status(self, name: str, score: float) -> NodeStatus:
        """Xác định trạng thái tổng thể của node"""
        name_lower = name.lower()

        # Kiểm tra chỉ báo trạng thái rõ ràng
        if any(keyword in name_lower for keyword in self.approved_keywords):
            return NodeStatus.APPROVED if score >= 0.8 else NodeStatus.REVIEW

        if any(keyword in name_lower for keyword in self.wip_keywords):
            return NodeStatus.DRAFT

        # Phân loại theo điểm số
        if score >= 0.9:
            return NodeStatus.READY
        elif score >= 0.8:
            return NodeStatus.APPROVED
        elif score >= 0.6:
            return NodeStatus.REVIEW
        else:
            return NodeStatus.DRAFT