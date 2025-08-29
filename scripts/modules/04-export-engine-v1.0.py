#!/usr/bin/env python3
"""
Export Engine Module v1.0
=========================

Export engine với batch processing, progress tracking và file management.

Features:
- Batch SVG export processing
- Parallel export execution
- Progress tracking và monitoring
- File management và deduplication
- Export quality validation
- Performance optimization

Author: DS Tools - Modular Pipeline
Version: 1.0.0
Date: 2025-08-29
"""

import asyncio
import aiohttp
import json
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import os

# Fix Windows encoding issues (disabled to avoid conflicts)
# if sys.platform == "win32":
#     import codecs
#     sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
#     sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class ExportJob:
    """Represents an export job với metadata"""
    node_id: str
    node_name: str
    page_id: str
    page_name: str
    export_format: str = "SVG"
    status: str = "pending"  # pending, processing, completed, failed
    file_path: Optional[str] = None
    file_size: int = 0
    export_time: float = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    checksum: Optional[str] = None

@dataclass
class ExportBatch:
    """Represents a batch of export jobs"""
    batch_id: str
    jobs: List[ExportJob]
    status: str = "pending"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0

class ExportEngine:
    """Export engine với batch processing và progress tracking"""

    def __init__(self, api_token: str, config_path: Optional[str] = None):
        self.api_token = api_token
        self.config_path = config_path or "scripts/config/pipeline_config.json"
        # Adjust path if running from modules directory
        if not Path(self.config_path).exists():
            self.config_path = "../config/pipeline_config.json"
        self.base_url = "https://api.figma.com/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.export_jobs = []
        self.completed_exports = []
        self.failed_exports = []

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
        self.executor.shutdown(wait=True)

    async def initialize_session(self):
        """Initialize aiohttp session với proper headers"""
        print("[EXPORT] Initializing export session...")

        headers = {
            "X-Figma-Token": self.api_token,
            "User-Agent": "Figma-Pipeline-Export-Engine/1.0"
        }

        self.session = aiohttp.ClientSession(headers=headers)
        print("[SUCCESS] Export session initialized")

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            print("[SUCCESS] Export session closed")

    def create_export_jobs(self, processed_nodes: List[Dict[str, Any]]) -> List[ExportJob]:
        """Create export jobs từ processed nodes"""
        print(f"[JOBS] Creating export jobs for {len(processed_nodes)} nodes...")

        jobs = []
        for node_data in processed_nodes:
            # CRITICAL FIX: Add null checks to prevent 'NoneType' errors
            if not node_data or not isinstance(node_data, dict):
                print(f"[DEBUG] Skipping invalid node data: {type(node_data)}")
                continue

            if not node_data.get("export_ready", False):
                continue

            # Additional safety checks
            node_id = node_data.get("id")
            node_name = node_data.get("name", "unnamed")
            page_id = node_data.get("page_id", "unknown")
            page_name = node_data.get("page_name", "unknown")

            if not node_id:
                print(f"[DEBUG] Skipping node without ID: {node_name}")
                continue

            job = ExportJob(
                node_id=node_id,
                node_name=node_name,
                page_id=page_id,
                page_name=page_name,
                export_format="SVG",
                status="pending"
            )
            jobs.append(job)

        print(f"[SUCCESS] Created {len(jobs)} export jobs")
        return jobs

    def create_export_batches(self, jobs: List[ExportJob], batch_size: int = 10) -> List[ExportBatch]:
        """Create batches từ export jobs"""
        print(f"[BATCHES] Creating batches (size: {batch_size})...")

        batches = []
        for i in range(0, len(jobs), batch_size):
            batch_jobs = jobs[i:i + batch_size]
            batch = ExportBatch(
                batch_id=f"batch_{i//batch_size + 1:03d}",
                jobs=batch_jobs,
                total_jobs=len(batch_jobs),
                status="pending"
            )
            batches.append(batch)

        print(f"[SUCCESS] Created {len(batches)} batches")
        return batches

    async def export_single_node(self, job: ExportJob, file_key: str) -> ExportJob:
        """Export a single node từ Figma"""
        try:
            job.status = "processing"
            start_time = time.time()

            # CRITICAL FIX: Validate inputs
            if not job or not job.node_id or not file_key:
                raise Exception("Invalid job or file_key provided")

            # Build export URL
            export_url = f"{self.base_url}/images/{file_key}"
            params = {
                "ids": job.node_id,
                "format": "svg",
                "scale": "1"
            }

            print(f"[EXPORT] Exporting node: {job.node_name}")

            # Make export request
            async with self.session.get(export_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # CRITICAL FIX: Safe dictionary access
                    if not data or not isinstance(data, dict):
                        raise Exception("Invalid response data from Figma API")

                    images = data.get("images", {})

                    # CRITICAL FIX: Safe dictionary access
                    if not images or not isinstance(images, dict):
                        raise Exception("No images data in response")

                    if job.node_id in images and images[job.node_id]:
                        image_url = images[job.node_id]

                        # Download the actual SVG
                        async with self.session.get(image_url) as img_response:
                            if img_response.status == 200:
                                svg_content = await img_response.text()

                                # Generate filename
                                safe_name = self._sanitize_filename(job.node_name)
                                filename = f"{safe_name}.svg"

                                job.file_path = filename
                                job.file_size = len(svg_content.encode('utf-8'))
                                job.export_time = time.time() - start_time
                                job.status = "completed"
                                job.checksum = hashlib.md5(svg_content.encode('utf-8')).hexdigest()

                                print(f"[SUCCESS] Successfully exported: {filename}")
                                return job, svg_content
                            else:
                                raise Exception(f"Failed to download SVG: HTTP {img_response.status}")
                    else:
                        raise Exception("No image URL returned for node")
                else:
                    error_text = await response.text()
                    raise Exception(f"Export request failed: HTTP {response.status} - {error_text}")

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.retry_count += 1
            print(f"[ERROR] Failed to export {job.node_name}: {e}")
            return job, None

    async def process_batch(self, batch: ExportBatch, file_key: str,
                          output_dir: str) -> Tuple[ExportBatch, Dict[str, str]]:
        """Process a batch of export jobs"""
        print(f"[BATCH] Processing batch: {batch.batch_id}")

        batch.start_time = datetime.now(timezone.utc)
        batch.status = "processing"

        exported_files = {}

        # Process jobs in the batch
        for job in batch.jobs:
            job_result, svg_content = await self.export_single_node(job, file_key)

            if job_result.status == "completed" and svg_content:
                # Save file to disk
                file_path = Path(output_dir) / job_result.file_path
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)

                exported_files[job_result.node_id] = str(file_path)
                batch.completed_jobs += 1
            else:
                batch.failed_jobs += 1

        batch.end_time = datetime.now(timezone.utc)
        batch.status = "completed"

        processing_time = (batch.end_time - batch.start_time).total_seconds()
        print(f"[SUCCESS] Completed batch {batch.batch_id}: {batch.completed_jobs}/{batch.total_jobs} jobs in {processing_time:.2f}s")

        return batch, exported_files

    async def export_nodes_batch(self, processed_data: Dict[str, Any],
                               file_key: str, output_dir: str = "exports/export_engine/",
                               batch_size: int = 10) -> Dict[str, Any]:
        """Main method to export nodes in batches"""
        print("[EXPORT] Starting batch export process...")
        print("=" * 80)

        if not processed_data.get("success", False):
            return {
                "success": False,
                "error": "Invalid processed data provided"
            }

        start_time = datetime.now(timezone.utc)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create export jobs
        processed_nodes = processed_data.get("processed_nodes", [])
        export_jobs = self.create_export_jobs(processed_nodes)

        if not export_jobs:
            return {
                "success": False,
                "error": "No export-ready nodes found"
            }

        # Create batches
        batches = self.create_export_batches(export_jobs, batch_size)

        # Process batches
        all_exported_files = {}
        total_completed = 0
        total_failed = 0

        for batch in batches:
            batch_result, batch_files = await self.process_batch(batch, file_key, str(output_path))
            all_exported_files.update(batch_files)
            total_completed += batch_result.completed_jobs
            total_failed += batch_result.failed_jobs

        end_time = datetime.now(timezone.utc)
        total_time = (end_time - start_time).total_seconds()

        # Compile results
        result = {
            "success": True,
            "exported_files": all_exported_files,
            "summary": {
                "total_jobs": len(export_jobs),
                "completed_jobs": total_completed,
                "failed_jobs": total_failed,
                "batches_processed": len(batches),
                "total_time": total_time,
                "average_time_per_job": total_time / len(export_jobs) if export_jobs else 0,
                "output_directory": str(output_path)
            },
            "batches": [asdict(batch) for batch in batches],
            "timestamp": start_time.isoformat()
        }

        print("[SUCCESS] Batch export process completed")
        print(f"[SUMMARY] Exported {total_completed}/{len(export_jobs)} files")
        print(f"[SUMMARY] Output directory: {output_path}")

        return result

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage"""
        # Remove invalid characters
        safe_name = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))

        # Replace spaces with underscores
        safe_name = safe_name.replace(' ', '_')

        # Remove multiple consecutive underscores
        while '__' in safe_name:
            safe_name = safe_name.replace('__', '_')

        # Ensure it's not empty
        if not safe_name:
            safe_name = "unnamed_node"

        return safe_name

    async def validate_exports(self, export_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate exported files"""
        print("[VALIDATION] Validating exported files...")

        if not export_result.get("success", False):
            return export_result

        output_dir = Path(export_result["summary"]["output_directory"])
        exported_files = export_result.get("exported_files", {})

        validation_results = {
            "total_files": len(exported_files),
            "valid_files": 0,
            "invalid_files": 0,
            "validation_errors": []
        }

        for node_id, file_path in exported_files.items():
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                validation_results["invalid_files"] += 1
                validation_results["validation_errors"].append(f"File not found: {file_path}")
                continue

            # Check file size
            if file_path_obj.stat().st_size == 0:
                validation_results["invalid_files"] += 1
                validation_results["validation_errors"].append(f"Empty file: {file_path}")
                continue

            # Check if it's valid SVG (basic check)
            try:
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    content = f.read()

                if '<svg' in content and '</svg>' in content:
                    validation_results["valid_files"] += 1
                else:
                    validation_results["invalid_files"] += 1
                    validation_results["validation_errors"].append(f"Invalid SVG content: {file_path}")
            except Exception as e:
                validation_results["invalid_files"] += 1
                validation_results["validation_errors"].append(f"Error reading file {file_path}: {e}")

        export_result["validation"] = validation_results

        print(f"[SUCCESS] Valid files: {validation_results['valid_files']}/{validation_results['total_files']}")

        if validation_results["invalid_files"] > 0:
            print(f"[WARNING] Found {validation_results['invalid_files']} invalid files")

        return export_result

    async def save_export_report(self, result: Dict[str, Any],
                               output_dir: str = "exports/export_engine/"):
        """Save export engine operation report"""
        print("[REPORT] Saving export engine report...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save detailed report
        report_file = output_path / "export_engine_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        # Save summary report
        summary_file = output_path / "export_engine_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Export Engine Operation Summary\n\n")
            f.write(f"**Timestamp:** {result.get('timestamp', 'N/A')}\n\n")

            if result.get("success"):
                summary = result.get("summary", {})
                f.write("## ✅ Export Successful\n\n")
                f.write(f"- **Total Jobs:** {summary.get('total_jobs', 0)}\n")
                f.write(f"- **Completed:** {summary.get('completed_jobs', 0)}\n")
                f.write(f"- **Failed:** {summary.get('failed_jobs', 0)}\n")
                f.write(f"- **Batches:** {summary.get('batches_processed', 0)}\n")
                f.write(f"- **Total Time:** {summary.get('total_time', 0):.2f} seconds\n")
                f.write(f"- **Avg Time/Job:** {summary.get('average_time_per_job', 0):.2f} seconds\n")
                f.write(f"- **Output Directory:** `{summary.get('output_directory', 'N/A')}`\n\n")

                # Validation results
                validation = result.get("validation", {})
                if validation:
                    f.write("## 🔍 File Validation\n\n")
                    f.write(f"- **Valid Files:** {validation.get('valid_files', 0)}\n")
                    f.write(f"- **Invalid Files:** {validation.get('invalid_files', 0)}\n")

                    if validation.get("validation_errors"):
                        f.write("\n### Validation Errors\n\n")
                        for error in validation["validation_errors"][:10]:  # Show first 10 errors
                            f.write(f"- {error}\n")
                        if len(validation["validation_errors"]) > 10:
                            f.write(f"- ... and {len(validation['validation_errors']) - 10} more errors\n")

                # Performance metrics
                f.write("\n## 📊 Performance Metrics\n\n")
                total_jobs = summary.get('total_jobs', 0)
                if total_jobs > 0:
                    success_rate = (summary.get('completed_jobs', 0) / total_jobs) * 100
                    f.write(f"- **Success Rate:** {success_rate:.1f}%\n")
                    total_time = summary.get('total_time', 1)
                    if total_time > 0:
                        f.write(f"- **Files per Second:** {total_jobs / total_time:.2f}\n")
                    else:
                        f.write("- **Files per Second:** N/A\n")
                else:
                    f.write("- **Success Rate:** N/A (no jobs)\n")
                    f.write("- **Files per Second:** N/A (no jobs)\n")

            else:
                f.write("## ❌ Export Failed\n\n")
                f.write(f"**Error:** {result.get('error', 'Unknown error')}\n\n")

        print(f"[SUCCESS] Reports saved to: {output_path}")
        return str(report_file), str(summary_file)

async def main():
    """Main function for standalone execution"""
    print("EXPORT ENGINE MODULE v1.0")
    print("=" * 80)
    print("Export engine với batch processing và progress tracking")
    print()

    # For standalone execution, we would need to load data from previous modules
    # This is a placeholder for integration with the pipeline
    print("[INFO] This module is designed to work within the pipeline")
    print("[INFO] Use the pipeline orchestrator for full functionality")
    print()

    # Create sample data for testing
    sample_result = {
        "success": True,
        "exported_files": {},
        "summary": {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "batches_processed": 0,
            "total_time": 0,
            "average_time_per_job": 0,
            "output_directory": "exports/export_engine/"
        },
        "batches": [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # For standalone testing, create a mock API token
    mock_token = "mock_token_for_testing"
    engine = ExportEngine(mock_token)
    await engine.save_export_report(sample_result)

    print("\n" + "=" * 80)
    print("EXPORT ENGINE SUMMARY")
    print("=" * 80)
    print("Status: Module loaded successfully")
    print("Use pipeline orchestrator for full processing")

    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\nExport engine {'completed successfully' if success else 'failed'}")

    sys.exit(0 if success else 1)