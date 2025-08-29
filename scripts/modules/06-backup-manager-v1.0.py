#!/usr/bin/env python3
"""
Backup Manager Module v1.0
==========================

Backup và cleanup management với rollback capabilities.

Features:
- Directory backup với timestamp
- Incremental backup strategies
- Cleanup operations
- Rollback capabilities
- Backup validation
- Storage management

Author: DS Tools - Modular Pipeline
Version: 1.0.0
Date: 2025-08-29
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Fix Windows encoding issues (disabled to avoid conflicts)
# if sys.platform == "win32":
#     import codecs
#     sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
#     sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class BackupManager:
    """Backup và cleanup management với rollback capabilities"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "scripts/config/pipeline_config.json"
        # Adjust path if running from modules directory
        if not Path(self.config_path).exists():
            self.config_path = "../config/pipeline_config.json"
        self.backup_registry = {}
        self.cleanup_registry = {}

    async def load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration"""
        print("[CONFIG] Loading pipeline configuration...")

        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print("[SUCCESS] Configuration loaded successfully")
        return config

    def generate_backup_id(self, source_path: str) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        source_name = Path(source_path).name
        backup_id = f"{source_name}_backup_{timestamp}"
        return backup_id

    def calculate_directory_hash(self, directory_path: Path) -> str:
        """Calculate hash của directory contents"""
        hash_md5 = hashlib.md5()

        if not directory_path.exists():
            return ""

        # Sort files for consistent hashing
        file_paths = []
        for file_path in sorted(directory_path.rglob('*')):
            if file_path.is_file():
                file_paths.append(file_path)

        for file_path in file_paths:
            # Add relative path to hash
            relative_path = file_path.relative_to(directory_path)
            hash_md5.update(str(relative_path).encode('utf-8'))

            # Add file content to hash
            try:
                with open(file_path, 'rb') as f:
                    while True:
                        data = f.read(65536)  # 64KB chunks
                        if not data:
                            break
                        hash_md5.update(data)
            except Exception:
                # If file can't be read, just hash the path
                hash_md5.update(b"unreadable")

        return hash_md5.hexdigest()

    async def create_directory_backup(self, source_path: str,
                                    backup_base_dir: str = "exports/backups/",
                                    backup_type: str = "full") -> Dict[str, Any]:
        """Create backup của directory"""
        print(f"[BACKUP] Creating {backup_type} backup of: {source_path}")

        source_path_obj = Path(source_path)
        backup_base_obj = Path(backup_base_dir)

        if not source_path_obj.exists():
            return {
                "success": False,
                "error": f"Source directory does not exist: {source_path}",
                "backup_id": None,
                "backup_path": None
            }

        # Create backup base directory
        backup_base_obj.mkdir(parents=True, exist_ok=True)

        # Generate backup ID và path
        backup_id = self.generate_backup_id(source_path)
        backup_path = backup_base_obj / backup_id

        try:
            # Calculate source hash before backup
            source_hash = self.calculate_directory_hash(source_path_obj)

            # Create backup
            if backup_type == "full":
                shutil.copytree(source_path, backup_path)
            elif backup_type == "incremental":
                # For incremental, only copy changed files (simplified version)
                self._create_incremental_backup(source_path_obj, backup_path)
            else:
                raise ValueError(f"Unsupported backup type: {backup_type}")

            # Calculate backup hash for verification
            backup_hash = self.calculate_directory_hash(backup_path)

            # Create backup metadata
            metadata = {
                "backup_id": backup_id,
                "source_path": str(source_path_obj),
                "backup_path": str(backup_path),
                "backup_type": backup_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_hash": source_hash,
                "backup_hash": backup_hash,
                "verification_status": source_hash == backup_hash,
                "file_count": sum(1 for _ in backup_path.rglob('*') if _.is_file()),
                "total_size": sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            }

            # Save metadata
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # Register backup
            self.backup_registry[backup_id] = metadata

            print("[SUCCESS] Backup created successfully")
            print(f"[BACKUP] Backup location: {backup_path}")
            print(f"[BACKUP] Files backed up: {metadata['file_count']}")
            print(f"[BACKUP] Total size: {metadata['total_size'] / 1024:.1f} KB")

            return {
                "success": True,
                "backup_id": backup_id,
                "backup_path": str(backup_path),
                "metadata": metadata
            }

        except Exception as e:
            # Cleanup failed backup
            if backup_path.exists():
                shutil.rmtree(backup_path)

            print(f"[ERROR] Backup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "backup_id": backup_id,
                "backup_path": str(backup_path)
            }

    def _create_incremental_backup(self, source_path: Path, backup_path: Path):
        """Create incremental backup (simplified implementation)"""
        # For now, just copy everything (can be enhanced with actual incremental logic)
        shutil.copytree(source_path, backup_path)

    async def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """Verify backup integrity"""
        print(f"[VERIFY] Verifying backup: {backup_id}")

        if backup_id not in self.backup_registry:
            return {
                "success": False,
                "error": f"Backup not found in registry: {backup_id}"
            }

        metadata = self.backup_registry[backup_id]
        backup_path = Path(metadata["backup_path"])

        if not backup_path.exists():
            return {
                "success": False,
                "error": f"Backup directory does not exist: {backup_path}"
            }

        # Verify metadata file exists
        metadata_file = backup_path / "backup_metadata.json"
        if not metadata_file.exists():
            return {
                "success": False,
                "error": "Backup metadata file missing"
            }

        # Recalculate hash
        current_hash = self.calculate_directory_hash(backup_path)
        original_hash = metadata.get("backup_hash", "")

        # Verify file count
        current_file_count = sum(1 for _ in backup_path.rglob('*') if _.is_file())
        original_file_count = metadata.get("file_count", 0)

        verification = {
            "hash_match": current_hash == original_hash,
            "file_count_match": current_file_count == original_file_count,
            "metadata_exists": True,
            "directory_exists": True
        }

        overall_success = all(verification.values())

        result = {
            "success": overall_success,
            "backup_id": backup_id,
            "verification": verification,
            "current_hash": current_hash,
            "original_hash": original_hash,
            "current_file_count": current_file_count,
            "original_file_count": original_file_count
        }

        if overall_success:
            print("[SUCCESS] Backup verification passed")
        else:
            print("[ERROR] Backup verification failed")
            for check, passed in verification.items():
                if not passed:
                    print(f"   - {check}: FAILED")

        return result

    async def rollback_from_backup(self, backup_id: str, target_path: str,
                                 create_backup: bool = True) -> Dict[str, Any]:
        """Rollback to backup"""
        print(f"[ROLLBACK] Rolling back to backup: {backup_id}")

        if backup_id not in self.backup_registry:
            return {
                "success": False,
                "error": f"Backup not found in registry: {backup_id}"
            }

        metadata = self.backup_registry[backup_id]
        backup_path = Path(metadata["backup_path"])
        target_path_obj = Path(target_path)

        if not backup_path.exists():
            return {
                "success": False,
                "error": f"Backup directory does not exist: {backup_path}"
            }

        try:
            # Create backup of current state if requested
            if create_backup and target_path_obj.exists():
                current_backup_result = await self.create_directory_backup(
                    str(target_path_obj),
                    backup_type="rollback_backup"
                )
                if not current_backup_result["success"]:
                    print(f"[WARNING] Failed to backup current state: {current_backup_result['error']}")

            # Remove target directory if exists
            if target_path_obj.exists():
                shutil.rmtree(target_path_obj)

            # Restore from backup
            shutil.copytree(backup_path, target_path_obj)

            print("[SUCCESS] Rollback completed successfully")
            print(f"[ROLLBACK] Restored to: {target_path}")

            return {
                "success": True,
                "backup_id": backup_id,
                "target_path": target_path,
                "rollback_timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            print(f"[ERROR] Rollback failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "backup_id": backup_id,
                "target_path": target_path
            }

    async def cleanup_old_backups(self, backup_base_dir: str = "exports/backups/",
                                max_backups: int = 10,
                                max_age_days: int = 30) -> Dict[str, Any]:
        """Cleanup old backups"""
        print("[CLEANUP] Starting backup cleanup...")

        backup_base_obj = Path(backup_base_dir)
        if not backup_base_obj.exists():
            return {
                "success": True,
                "message": "No backup directory found",
                "cleaned_backups": []
            }

        # Find all backup directories
        backup_dirs = []
        for item in backup_base_obj.iterdir():
            if item.is_dir() and "backup" in item.name:
                metadata_file = item / "backup_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        backup_dirs.append({
                            "path": item,
                            "metadata": metadata,
                            "age_days": (datetime.now(timezone.utc) - datetime.fromisoformat(metadata["timestamp"].replace('Z', '+00:00'))).days
                        })
                    except Exception:
                        # If metadata can't be read, still include for cleanup
                        backup_dirs.append({
                            "path": item,
                            "metadata": None,
                            "age_days": 999  # Very old
                        })

        # Sort by timestamp (newest first)
        backup_dirs.sort(key=lambda x: x["metadata"]["timestamp"] if x["metadata"] else "1970-01-01", reverse=True)

        # Identify backups to clean
        to_clean = []

        # Remove backups beyond max count
        if len(backup_dirs) > max_backups:
            to_clean.extend(backup_dirs[max_backups:])

        # Remove backups older than max age
        for backup in backup_dirs:
            if backup["age_days"] > max_age_days:
                if backup not in to_clean:
                    to_clean.append(backup)

        # Perform cleanup
        cleaned_backups = []
        for backup in to_clean:
            try:
                shutil.rmtree(backup["path"])
                cleaned_backups.append(str(backup["path"]))
                print(f"[CLEANUP] Removed backup: {backup['path']}")
            except Exception as e:
                print(f"[WARNING] Failed to remove {backup['path']}: {e}")

        print(f"[SUCCESS] Cleanup completed. Removed {len(cleaned_backups)} backups")

        return {
            "success": True,
            "total_backups": len(backup_dirs),
            "cleaned_backups": cleaned_backups,
            "remaining_backups": len(backup_dirs) - len(cleaned_backups)
        }

    async def get_backup_inventory(self, backup_base_dir: str = "exports/backups/") -> Dict[str, Any]:
        """Get inventory of all backups"""
        print("[INVENTORY] Generating backup inventory...")

        backup_base_obj = Path(backup_base_dir)
        inventory = {
            "backup_base_dir": str(backup_base_obj),
            "backups": [],
            "summary": {
                "total_backups": 0,
                "total_size": 0,
                "oldest_backup": None,
                "newest_backup": None
            }
        }

        if not backup_base_obj.exists():
            print("[INFO] No backup directory found")
            return inventory

        # Scan backup directories
        for item in backup_base_obj.iterdir():
            if item.is_dir() and "backup" in item.name:
                metadata_file = item / "backup_metadata.json"
                backup_info = {
                    "backup_id": item.name,
                    "path": str(item),
                    "metadata": None,
                    "size": 0,
                    "file_count": 0
                }

                # Try to read metadata
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            backup_info["metadata"] = json.load(f)
                    except Exception:
                        pass

                # Calculate size
                if item.exists():
                    backup_info["size"] = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    backup_info["file_count"] = sum(1 for _ in item.rglob('*') if _.is_file())

                inventory["backups"].append(backup_info)
                inventory["summary"]["total_size"] += backup_info["size"]

        # Sort backups by timestamp
        inventory["backups"].sort(
            key=lambda x: x["metadata"]["timestamp"] if x["metadata"] else "1970-01-01",
            reverse=True
        )

        inventory["summary"]["total_backups"] = len(inventory["backups"])

        if inventory["backups"]:
            inventory["summary"]["newest_backup"] = inventory["backups"][0]["backup_id"]
            inventory["summary"]["oldest_backup"] = inventory["backups"][-1]["backup_id"]

        print(f"[SUCCESS] Found {len(inventory['backups'])} backups")
        return inventory

    async def save_backup_report(self, result: Dict[str, Any],
                               output_dir: str = "exports/backup_manager/"):
        """Save backup operation report"""
        print("[REPORT] Saving backup report...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save detailed report
        report_file = output_path / "backup_manager_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        # Save summary report
        summary_file = output_path / "backup_manager_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Backup Manager Operation Summary\n\n")
            f.write(f"**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")

            if result.get("success"):
                f.write("## ✅ Operation Successful\n\n")
                f.write(f"- **Backup ID:** {result.get('backup_id', 'N/A')}\n")
                f.write(f"- **Backup Path:** `{result.get('backup_path', 'N/A')}`\n")
                f.write(f"- **Backup Type:** {result.get('metadata', {}).get('backup_type', 'N/A')}\n")
                f.write(f"- **Files Backed Up:** {result.get('metadata', {}).get('file_count', 0)}\n")
                f.write(f"- **Total Size:** {result.get('metadata', {}).get('total_size', 0) / 1024:.1f} KB\n")
                f.write(f"- **Verification:** {'✅ Passed' if result.get('metadata', {}).get('verification_status') else '❌ Failed'}\n")
            else:
                f.write("## ❌ Operation Failed\n\n")
                f.write(f"**Error:** {result.get('error', 'Unknown error')}\n\n")

        print(f"[SUCCESS] Reports saved to: {output_path}")
        return str(report_file), str(summary_file)

async def main():
    """Main function for standalone execution"""
    print("BACKUP MANAGER MODULE v1.0")
    print("=" * 80)
    print("Backup và cleanup management với rollback capabilities")
    print()

    # For standalone execution, create sample operations
    print("[INFO] This module is designed to work within the pipeline")
    print("[INFO] Use the pipeline orchestrator for full functionality")
    print()

    # Create sample backup operation
    manager = BackupManager()

    # Create a test directory for demonstration
    test_dir = Path("exports/test_backup_source")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create some test files
    (test_dir / "test_file_1.txt").write_text("Test content 1")
    (test_dir / "test_file_2.txt").write_text("Test content 2")
    (test_dir / "subdir").mkdir(exist_ok=True)
    (test_dir / "subdir" / "test_file_3.txt").write_text("Test content 3")

    # Perform backup
    result = await manager.create_directory_backup(str(test_dir))
    await manager.save_backup_report(result)

    # Cleanup test directory
    shutil.rmtree(test_dir)

    print("\n" + "=" * 80)
    print("BACKUP MANAGER SUMMARY")
    print("=" * 80)
    print("Status: Module loaded successfully")
    print("Use pipeline orchestrator for full processing")

    return True

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    print(f"\nBackup manager {'completed successfully' if success else 'failed'}")

    sys.exit(0 if success else 1)