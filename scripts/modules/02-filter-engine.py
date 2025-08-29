#!/usr/bin/env python3
"""
Filter Engine Module v1.0
=========================

Node filtering engine với pattern matching và criteria-based selection.
Supports include/exclude patterns, case sensitivity, và advanced filtering.

Features:
- Pattern-based node filtering
- Include/exclude logic
- Case-sensitive/insensitive matching
- Wildcard pattern support (*)
- Comprehensive result reporting
- Unicode-safe operations

Author: Kilo Code Debug Agent
Version: 1.0.0
Date: 2025-08-29
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, NamedTuple
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class FilterCriteria(NamedTuple):
    """Filter criteria configuration"""
    include: List[str]
    exclude: List[str]
    case_sensitive: bool

@dataclass
class FilterResult:
    """Result of filtering operation"""
    success: bool
    pages: List[Dict[str, Any]]
    total_pages: int
    total_nodes: int
    filter_criteria: FilterCriteria
    error: Optional[str] = None

class FilterEngine:
    """Node filtering engine với pattern matching capabilities"""

    def __init__(self, config_manager=None):
        """
        Initialize filter engine

        Args:
            config_manager: Config manager instance (optional)
        """
        self.config_manager = config_manager
        print(f"[DEBUG] [FILTER_ENGINE] FilterEngine initialized")

    def _compile_pattern(self, pattern: str, case_sensitive: bool) -> re.Pattern:
        """
        Compile regex pattern từ wildcard pattern

        Args:
            pattern: Wildcard pattern (e.g., "svg_exporter_*")
            case_sensitive: Whether pattern matching should be case sensitive

        Returns:
            Compiled regex pattern
        """
        # Escape special regex characters except *
        escaped = re.escape(pattern)
        # Replace escaped * with .*
        regex_pattern = escaped.replace(r'\*', '.*')

        flags = 0 if case_sensitive else re.IGNORECASE
        return re.compile(f"^{regex_pattern}$", flags)

    def _matches_any_pattern(self, text: str, patterns: List[str], case_sensitive: bool) -> bool:
        """
        Check if text matches any of the given patterns

        Args:
            text: Text to check
            patterns: List of wildcard patterns
            case_sensitive: Case sensitivity flag

        Returns:
            True if text matches any pattern
        """
        if not patterns:
            return False

        for pattern in patterns:
            compiled_pattern = self._compile_pattern(pattern, case_sensitive)
            if compiled_pattern.match(text):
                return True

        return False

    def _should_include_node(self, node_name: str, include_patterns: List[str],
                           exclude_patterns: List[str], case_sensitive: bool) -> bool:
        """
        Determine if a node should be included based on filter criteria

        Args:
            node_name: Name of the node
            include_patterns: Patterns that nodes must match
            exclude_patterns: Patterns that nodes must NOT match
            case_sensitive: Case sensitivity flag

        Returns:
            True if node should be included
        """
        # If no include patterns specified, include all nodes
        if not include_patterns:
            should_include = True
        else:
            # Must match at least one include pattern
            should_include = self._matches_any_pattern(node_name, include_patterns, case_sensitive)

        # If should be included but matches exclude pattern, exclude it
        if should_include and exclude_patterns:
            if self._matches_any_pattern(node_name, exclude_patterns, case_sensitive):
                should_include = False

        return should_include

    def filter_nodes_by_criteria(self, pages_data: Dict[str, Any],
                               include_patterns: Optional[List[str]] = None,
                               exclude_patterns: Optional[List[str]] = None,
                               case_sensitive: Optional[bool] = None) -> FilterResult:
        """
        Filter nodes based on specified criteria

        Args:
            pages_data: Raw pages data from API
            include_patterns: Patterns to include (optional)
            exclude_patterns: Patterns to exclude (optional)
            case_sensitive: Case sensitivity flag (optional)

        Returns:
            FilterResult object with filtered data
        """
        try:
            print(f"[DEBUG] [FILTER_ENGINE] Starting node filtering")

            # Get default patterns from config if not provided
            if include_patterns is None and self.config_manager:
                config_patterns = self.config_manager.get_filter_patterns()
                include_patterns = config_patterns.include
            elif include_patterns is None:
                include_patterns = []

            if exclude_patterns is None and self.config_manager:
                config_patterns = self.config_manager.get_filter_patterns()
                exclude_patterns = config_patterns.exclude
            elif exclude_patterns is None:
                exclude_patterns = []

            if case_sensitive is None and self.config_manager:
                config_patterns = self.config_manager.get_filter_patterns()
                case_sensitive = config_patterns.case_sensitive
            elif case_sensitive is None:
                case_sensitive = False

            # Create filter criteria
            filter_criteria = FilterCriteria(
                include=include_patterns,
                exclude=exclude_patterns,
                case_sensitive=case_sensitive
            )

            print(f"[DEBUG] [FILTER_ENGINE] Filter criteria:")
            print(f"  Include patterns: {include_patterns}")
            print(f"  Exclude patterns: {exclude_patterns}")
            print(f"  Case sensitive: {case_sensitive}")

            if not pages_data.get("success", False):
                return FilterResult(
                    success=False,
                    pages=[],
                    total_pages=0,
                    total_nodes=0,
                    filter_criteria=filter_criteria,
                    error="Invalid pages data provided"
                )

            # Process each page
            filtered_pages = []
            total_filtered_nodes = 0

            for page in pages_data.get("pages", []):
                page_id = page.get("id")
                page_name = page.get("name", "Unnamed Page")
                original_nodes = page.get("visible_nodes", [])

                # Filter nodes in this page
                filtered_nodes = []
                for node in original_nodes:
                    node_name = node.get("name", "")
                    node_type = node.get("type", "")

                    if self._should_include_node(node_name, include_patterns,
                                               exclude_patterns, case_sensitive):
                        filtered_nodes.append(node)
                        print(f"[DEBUG] [FILTER_ENGINE] INCLUDED: '{node_name}' (type: {node_type})")

                # Only include page if it has filtered nodes
                if filtered_nodes:
                    filtered_page = {
                        "id": page_id,
                        "name": page_name,
                        "node_count": len(filtered_nodes),
                        "visible_nodes": filtered_nodes
                    }
                    filtered_pages.append(filtered_page)
                    total_filtered_nodes += len(filtered_nodes)

                    print(f"[DEBUG] [FILTER_ENGINE] Page '{page_name}': {len(filtered_nodes)}/{len(original_nodes)} nodes")

            result = FilterResult(
                success=True,
                pages=filtered_pages,
                total_pages=len(filtered_pages),
                total_nodes=total_filtered_nodes,
                filter_criteria=filter_criteria
            )

            print(f"[DEBUG] [FILTER_ENGINE] Filtering completed:")
            print(f"  Total filtered pages: {result.total_pages}")
            print(f"  Total filtered nodes: {result.total_nodes}")

            return result

        except Exception as e:
            error_msg = f"Filter operation failed: {str(e)}"
            print(f"[DEBUG] [FILTER_ENGINE] {error_msg}")
            import traceback
            traceback.print_exc()

            return FilterResult(
                success=False,
                pages=[],
                total_pages=0,
                total_nodes=0,
                filter_criteria=FilterCriteria(include=[], exclude=[], case_sensitive=False),
                error=error_msg
            )

    def get_filter_statistics(self, original_data: Dict[str, Any],
                            filtered_result: FilterResult) -> Dict[str, Any]:
        """
        Generate statistics comparing original và filtered data

        Args:
            original_data: Original pages data
            filtered_result: Filtered result

        Returns:
            Statistics dictionary
        """
        try:
            original_pages = len(original_data.get("pages", []))
            original_nodes = original_data.get("total_nodes", 0)

            filtered_pages = filtered_result.total_pages
            filtered_nodes = filtered_result.total_nodes

            return {
                "original_pages": original_pages,
                "original_nodes": original_nodes,
                "filtered_pages": filtered_pages,
                "filtered_nodes": filtered_nodes,
                "pages_reduction": original_pages - filtered_pages,
                "nodes_reduction": original_nodes - filtered_nodes,
                "pages_reduction_percent": (original_pages - filtered_pages) / original_pages * 100 if original_pages > 0 else 0,
                "nodes_reduction_percent": (original_nodes - filtered_nodes) / original_nodes * 100 if original_nodes > 0 else 0,
                "filter_efficiency": filtered_nodes / original_nodes if original_nodes > 0 else 0
            }

        except Exception as e:
            print(f"[DEBUG] [FILTER_ENGINE] Error generating statistics: {str(e)}")
            return {
                "error": str(e),
                "original_pages": 0,
                "original_nodes": 0,
                "filtered_pages": 0,
                "filtered_nodes": 0
            }

# Export main classes
__all__ = ['FilterEngine', 'FilterResult', 'FilterCriteria']