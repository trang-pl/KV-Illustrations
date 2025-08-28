#!/usr/bin/env python3
"""
Enhanced Figma SVG Export System
===============================
Production-ready SVG exporter with change detection, dev-ready status,
and optimized batch processing.

Features:
- Change detection based on lastModified timestamps
- Dev-ready status assessment
- Optimized batch processing (10 nodes/batch)
- Smart caching and incremental exports
- Comprehensive monitoring and reporting

Author: DS Tools
Version: 2.0.0
Date: 2025-08-27
"""

import os
import sys
import json
import requests
import asyncio
import aiohttp
import base64
from datetime import datetime, timezone
from pathlib import Path
import time
import hashlib
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from config.settings import settings
import dotenv

# Load environment variables from .env
dotenv.load_dotenv()

# Load GITHUB_DATA_PATH from environment or .env
GITHUB_DATA_PATH = os.environ.get('GITHUB_DATA_PATH', './exports/')

# Load GitHub configuration from environment
GITHUB_PAT = os.environ.get('GITHUB_PAT')
GITHUB_REPO_OWNER = os.environ.get('GITHUB_REPO_OWNER')
GITHUB_REPO_NAME = os.environ.get('GITHUB_REPO_NAME')

# Ensure the directory exists
github_data_path_obj = Path(GITHUB_DATA_PATH)
github_data_path_obj.mkdir(parents=True, exist_ok=True)

# Configuration
DEFAULT_CONFIG = {
    "batch_size": 10,  # Optimized from testing
    "delay_between_batches": 1.5,  # Optimized from testing
    "max_concurrent_requests": 5,
    "retry_delay": 60,
    "max_retries": 3,
    "cache_duration": 3600,  # 1 hour cache
    "dev_ready_threshold": 0.8,  # 80% score for dev-ready
}


class NodeStatus(Enum):
    """Node development status"""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    READY = "ready"
    UNKNOWN = "unknown"


class ChangeStatus(Enum):
    """Node change status"""

    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


@dataclass
class NodeInfo:
    """Complete node information"""

    id: str
    name: str
    type: str
    width: float
    height: float
    last_modified: Optional[str]
    version: int
    path: str
    depth: int
    status: NodeStatus
    change_status: ChangeStatus
    dev_ready_score: float
    issues: List[str]
    exported_at: Optional[str] = None
    svg_size: Optional[int] = None


class ChangeDetector:
    """Detects changes in Figma nodes"""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.last_export_data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load previous export data from cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"📚 Loaded cache with {len(data.get('nodes', {}))} nodes")
                    return data
            except Exception as e:
                print(f"⚠️ Failed to load cache: {e}")
        return {"nodes": {}, "last_export": None, "file_version": None}

    def _save_cache(self, nodes: List[NodeInfo], file_version: str):
        """Save current export data to cache"""
        cache_data = {
            "nodes": {
                node.id: {
                    "name": node.name,
                    "last_modified": node.last_modified,
                    "version": node.version,
                    "exported_at": node.exported_at,
                    "dev_ready_score": node.dev_ready_score,
                    "status": node.status.value,
                    "svg_size": node.svg_size,
                }
                for node in nodes
            },
            "last_export": datetime.now().isoformat(),
            "file_version": file_version,
        }

        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Cache updated with {len(cache_data['nodes'])} nodes")
        except Exception as e:
            print(f"⚠️ Failed to save cache: {e}")

    def detect_changes(
        self, current_nodes: List[Dict], file_version: str
    ) -> Tuple[List[NodeInfo], Dict[str, int]]:
        """Detect changes and return updated node info"""
        changes_stats = {"new": 0, "modified": 0, "unchanged": 0, "deleted": 0}
        updated_nodes = []
        current_node_ids = set()

        for node_data in current_nodes:
            node_id = node_data["id"]
            current_node_ids.add(node_id)

            # Get cached data
            cached_node = self.last_export_data.get("nodes", {}).get(node_id, {})

            # Determine change status
            change_status = ChangeStatus.NEW
            if cached_node:
                current_modified = node_data.get("lastModified")
                cached_modified = cached_node.get("last_modified")
                current_version = node_data.get("version", 0)
                cached_version = cached_node.get("version", 0)

                if current_modified == cached_modified and current_version == cached_version:
                    change_status = ChangeStatus.UNCHANGED
                else:
                    change_status = ChangeStatus.MODIFIED

            # Create node info
            node_info = NodeInfo(
                id=node_id,
                name=node_data["name"],
                type=node_data["type"],
                width=node_data.get("absoluteBoundingBox", {}).get("width", 0),
                height=node_data.get("absoluteBoundingBox", {}).get("height", 0),
                last_modified=node_data.get("lastModified"),
                version=node_data.get("version", 0),
                path="",  # Will be set later based on export criteria
                depth=0,  # Will be calculated based on node hierarchy
                status=NodeStatus.UNKNOWN,  # Will be assessed later
                change_status=change_status,
                dev_ready_score=0.0,  # Will be calculated later
                issues=[],
            )
            updated_nodes.append(node_info)

            # Update change stats
            changes_stats[change_status.value] += 1

        # Handle deleted nodes
        cached_node_ids = set(self.last_export_data.get("nodes", {}).keys())
        deleted_ids = cached_node_ids - current_node_ids
        for deleted_id in deleted_ids:
            cached_node = self.last_export_data["nodes"][deleted_id]
            deleted_node = NodeInfo(
                id=deleted_id,
                name=cached_node["name"],
                type="DELETED",
                width=0,
                height=0,
                last_modified=None,
                version=cached_node.get("version", 0),
                path="",
                depth=0,
                status=NodeStatus.UNKNOWN,
                change_status=ChangeStatus.DELETED,
                dev_ready_score=0.0,
                issues=["Node deleted from Figma"],
            )
            updated_nodes.append(deleted_node)
            changes_stats["deleted"] += 1

        # Save updated cache
        self._save_cache(updated_nodes, file_version)

        return updated_nodes, changes_stats


@dataclass
class ExportConfig:
    """Configuration for export criteria"""

    export_type: str
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    naming_strategy: str = "default"
    duplicate_handling: str = "skip"  # skip, rename, overwrite
    metadata_path: Optional[str] = None
    output_dir: Optional[str] = None

    def __post_init__(self):
        if self.include_patterns is None:
            self.include_patterns = []
        if self.exclude_patterns is None:
            self.exclude_patterns = []
        if self.output_dir is None:
            self.output_dir = str(github_data_path_obj)


class ExportCriteriaProcessor:
    """Processes export criteria based on export_type"""

    def __init__(self, export_config: ExportConfig):
        self.config = export_config
        self.duplicate_tracker = {}  # Track duplicate names for prefixed exports

    def should_export_node(self, node_data: Dict) -> bool:
        """Determine if node should be exported based on criteria"""
        node_name = node_data.get("name", "")

        # Check exclude patterns first
        for pattern in self.config.exclude_patterns:
            if re.search(pattern, node_name, re.IGNORECASE):
                return False

        # Check include patterns if specified
        if self.config.include_patterns:
            for pattern in self.config.include_patterns:
                if re.search(pattern, node_name, re.IGNORECASE):
                    return True
            return False  # If include patterns specified but none match

        # Default logic based on export_type
        if self.config.export_type == "nodeID":
            return True  # Export all for nodeID type
        elif self.config.export_type.startswith("svg_exporter_"):
            return node_name.startswith("svg_exporter_")
        elif self.config.export_type.startswith("img_exporter_"):
            return node_name.startswith("img_exporter_")

        return True

    def get_export_name(self, node_data: Dict) -> str:
        """Get the export name based on naming strategy"""
        node_name = node_data.get("name", "")
        node_id = node_data.get("id", "")

        if self.config.export_type == "nodeID":
            # For nodeID type, use clean name without nodeID
            return self._clean_node_name(node_name)

        elif self.config.export_type.startswith("svg_exporter_"):
            # Extract name after prefix
            extracted_name = self._extract_prefixed_name(node_name, "svg_exporter_")
            return self._handle_duplicate_name(extracted_name, node_id, "svg")

        elif self.config.export_type.startswith("img_exporter_"):
            # Extract name after prefix
            extracted_name = self._extract_prefixed_name(node_name, "img_exporter_")
            return self._handle_duplicate_name(extracted_name, node_id, "png")

        return node_name

    def get_export_format(self) -> str:
        """Get export format based on export_type"""
        if self.config.export_type.startswith("svg_exporter_"):
            return "svg"
        elif self.config.export_type.startswith("img_exporter_"):
            return "png"
        return "svg"  # default

    def _clean_node_name(self, name: str) -> str:
        """Clean node name by removing nodeID suffix if present"""
        # Remove pattern like "_abc123" at the end
        cleaned = re.sub(r'_[a-zA-Z0-9]{6,}$', '', name)
        return cleaned.strip()

    def _extract_prefixed_name(self, name: str, prefix: str) -> str:
        """Extract name after prefix"""
        if name.startswith(prefix):
            return name[len(prefix):].strip()
        return name

    def _handle_duplicate_name(self, name: str, node_id: str, extension: str) -> str:
        """Handle duplicate names for prefixed exports"""
        if name not in self.duplicate_tracker:
            self.duplicate_tracker[name] = {
                "count": 1,
                "first_node_id": node_id,
                "extension": extension
            }
            return name
        else:
            # Duplicate found
            tracker = self.duplicate_tracker[name]
            tracker["count"] += 1

            if self.config.duplicate_handling == "skip":
                return None  # Skip this duplicate
            elif self.config.duplicate_handling == "rename":
                return f"{name}_{tracker['count'] - 1}"
            else:  # overwrite
                return name

    def get_duplicate_metadata(self) -> Dict[str, Any]:
        """Get metadata about duplicate names"""
        metadata = {}
        for name, info in self.duplicate_tracker.items():
            if info["count"] > 1:
                metadata[name] = {
                    "count": info["count"],
                    "first_node_id": info["first_node_id"],
                    "extension": info["extension"],
                    "duplicates": []  # Could be populated with node IDs
                }
        return metadata

    def save_duplicate_metadata(self):
        """Save duplicate metadata to file if configured"""
        if self.config.metadata_path:
            metadata = self.get_duplicate_metadata()
            try:
                with open(self.config.metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                print(f"📝 Duplicate metadata saved to {self.config.metadata_path}")
            except Exception as e:
                print(f"⚠️ Failed to save duplicate metadata: {e}")


class EnhancedFigmaExporter:
    """Enhanced Figma exporter with configurable export criteria"""

    def __init__(self, export_config: Dict[str, Any], cache_file: Path = None):
        self.export_config = ExportConfig(**export_config)
        self.criteria_processor = ExportCriteriaProcessor(self.export_config)

        if cache_file is None:
            cache_file = github_data_path_obj / "cache" / "figma_export_cache.json"
        self.change_detector = ChangeDetector(cache_file)
        self.output_dir = Path(self.export_config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_nodes(self, nodes_data: List[Dict], file_version: str) -> Dict[str, Any]:
        """Export nodes based on configurable criteria"""
        print(f"🚀 Starting export with type: {self.export_config.export_type}")

        # Filter nodes based on criteria
        filtered_nodes = []
        for node_data in nodes_data:
            if self.criteria_processor.should_export_node(node_data):
                filtered_nodes.append(node_data)

        print(f"📋 Filtered {len(filtered_nodes)} nodes from {len(nodes_data)} total")

        # Detect changes
        updated_nodes, changes_stats = self.change_detector.detect_changes(
            filtered_nodes, file_version
        )

        # Apply export criteria to node info
        processed_nodes = []
        for node_info in updated_nodes:
            if node_info.change_status != ChangeStatus.DELETED:
                # Find original node data
                original_data = next(
                    (n for n in filtered_nodes if n["id"] == node_info.id),
                    None
                )
                if original_data:
                    export_name = self.criteria_processor.get_export_name(original_data)
                    if export_name:  # Only add if not skipped due to duplicate
                        node_info.name = export_name
                        processed_nodes.append(node_info)

        # Save duplicate metadata
        self.criteria_processor.save_duplicate_metadata()

        result = {
            "export_type": self.export_config.export_type,
            "total_nodes": len(nodes_data),
            "filtered_nodes": len(filtered_nodes),
            "processed_nodes": len(processed_nodes),
            "changes": changes_stats,
            "export_format": self.criteria_processor.get_export_format(),
            "duplicate_metadata": self.criteria_processor.get_duplicate_metadata()
        }

        print(f"✅ Export completed: {result}")

        # GitHub push integration
        if (GITHUB_PAT and GITHUB_REPO_OWNER and GITHUB_REPO_NAME and
            result.get("processed_nodes", 0) > 0):
            print("🚀 Starting GitHub push...")
            github_service = GitHubPushService(GITHUB_PAT, GITHUB_REPO_OWNER, GITHUB_REPO_NAME)
            push_success = github_service.push_export_results(result)
            result["github_push_success"] = push_success
            if push_success:
                print("✅ GitHub push completed successfully")
            else:
                print("❌ GitHub push failed")
        else:
            print("⚠️ GitHub push skipped: missing configuration or no processed nodes")
            result["github_push_success"] = False

        return result


class GitHubPushService:
    """Service for pushing exported files to GitHub repository using GitHub API"""

    def __init__(self, github_pat: str, repo_owner: str, repo_name: str):
        self.github_pat = github_pat
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Authorization": f"Bearer {github_pat}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

    def get_username(self) -> str:
        """Get GitHub username from API"""
        try:
            response = requests.get("https://api.github.com/user", headers=self.headers)
            response.raise_for_status()
            user_data = response.json()
            return user_data.get("login", "")
        except requests.RequestException as e:
            print(f"❌ Failed to get GitHub username: {e}")
            return ""

    def get_file_sha(self, file_path: str) -> Optional[str]:
        """Get SHA of existing file in repository"""
        try:
            url = f"{self.base_url}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get("sha")
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            print(f"⚠️ Failed to get file SHA for {file_path}: {e}")
            return None

    def upload_file(self, local_path: Path, repo_path: str, commit_message: str) -> bool:
        """Upload a single file to GitHub repository"""
        try:
            # Read file content
            with open(local_path, "rb") as f:
                file_content = f.read()

            # Encode to base64
            encoded_content = base64.b64encode(file_content).decode("utf-8")

            # Prepare request data
            data = {
                "message": commit_message,
                "content": encoded_content
            }

            # Check if file exists to get SHA for update
            existing_sha = self.get_file_sha(repo_path)
            if existing_sha:
                data["sha"] = existing_sha

            # Upload file
            url = f"{self.base_url}/contents/{repo_path}"
            response = requests.put(url, headers=self.headers, json=data)
            response.raise_for_status()

            print(f"✅ Uploaded {local_path.name} to {repo_path}")
            return True

        except requests.RequestException as e:
            print(f"❌ Failed to upload {local_path.name}: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error uploading {local_path.name}: {e}")
            return False

    def upload_files_from_path(self, local_dir: Path, repo_base_path: str = "") -> Dict[str, Any]:
        """Upload all files from local directory to GitHub repository"""
        results = {
            "uploaded": [],
            "failed": [],
            "skipped": []
        }

        if not local_dir.exists():
            print(f"⚠️ Local directory {local_dir} does not exist")
            return results

        # Get username for commit message
        username = self.get_username()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Walk through all files in directory
        for file_path in local_dir.rglob("*"):
            if file_path.is_file():
                # Calculate relative path for repo
                relative_path = file_path.relative_to(local_dir)
                repo_path = f"{repo_base_path}/{relative_path}".lstrip("/")

                # Create commit message
                commit_message = f"Export Figma assets - {username} at {timestamp}"

                # Upload file
                if self.upload_file(file_path, repo_path, commit_message):
                    results["uploaded"].append(str(relative_path))
                else:
                    results["failed"].append(str(relative_path))

        print(f"📊 Upload summary: {len(results['uploaded'])} uploaded, {len(results['failed'])} failed")
        return results

    def push_export_results(self, export_result: Dict[str, Any]) -> bool:
        """Push export results to GitHub after successful export"""
        try:
            # Check if export was successful
            if export_result.get("processed_nodes", 0) == 0:
                print("⚠️ No nodes processed, skipping GitHub push")
                return False

            # Get local export directory
            local_dir = Path(GITHUB_DATA_PATH)

            # Create descriptive commit message
            changes = export_result.get("changes", {})
            new_count = changes.get("new", 0)
            modified_count = changes.get("modified", 0)
            export_type = export_result.get("export_type", "unknown")

            username = self.get_username()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            commit_message = f"Figma export: {export_type} - {new_count} new, {modified_count} modified - {username} at {timestamp}"

            # Upload files
            upload_results = self.upload_files_from_path(local_dir)

            if upload_results["uploaded"]:
                print(f"✅ GitHub push completed: {len(upload_results['uploaded'])} files uploaded")
                return True
            else:
                print("❌ GitHub push failed: no files uploaded")
                return False

        except Exception as e:
            print(f"❌ GitHub push failed with error: {e}")
            return False


def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python script.py <export_config_json>")
        sys.exit(1)

    try:
        export_config = json.loads(sys.argv[1])
        exporter = EnhancedFigmaExporter(export_config)

        # Example usage - in real implementation this would come from Figma API
        sample_nodes = [
            {"id": "1", "name": "svg_exporter_button", "type": "FRAME"},
            {"id": "2", "name": "img_exporter_icon", "type": "VECTOR"},
            {"id": "3", "name": "normal_component", "type": "COMPONENT"},
        ]

        result = exporter.export_nodes(sample_nodes, "v1.0")
        print(json.dumps(result, indent=2))

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON config: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
