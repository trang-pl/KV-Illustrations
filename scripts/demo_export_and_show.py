#!/usr/bin/env python3
"""
Demo Script: Run Figma export and display created files
Demo runs actual export with FIGMA_FILE_KEY from .env and shows files in GITHUB_DATA_PATH
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.services.figma_sync import FigmaSyncService
import dotenv

# Load environment variables
dotenv.load_dotenv()

async def demo_export_and_show():
    """Demo run export and display results"""
    print("DEMO: Export Figma and Show Files")
    print("=" * 60)

    # 1. Check FIGMA_FILE_KEY
    file_key = os.environ.get('FIGMA_FILE_KEY')
    if not file_key:
        print("[ERROR] FIGMA_FILE_KEY not found in .env")
        return False

    print(f"[FILE] File Key: {file_key}")

    # 2. Check GITHUB_DATA_PATH
    github_data_path = os.environ.get('GITHUB_DATA_PATH', './exports/')
    print(f"[PATH] Output Path: {github_data_path}")

    # 3. Create output directory
    output_dir = github_data_path
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 4. Initialize service
    print("\n[INIT] Initializing FigmaSyncService...")
    service = FigmaSyncService()

    # 5. Configure export
    root_node_id = "0:1"
    force_sync = True
    naming_filters = {
        "include_patterns": ["*"],  # Export all
        "exclude_patterns": [],
        "case_sensitive": False
    }

    print("\n[CONFIG] Export Configuration:")
    print(f"   Root Node: {root_node_id}")
    print(f"   Force Sync: {force_sync}")
    print(f"   Filters: {naming_filters}")

    try:
        # 6. Run export
        print("\n[EXPORT] Starting export...")
        result = await service.process_sync(
            file_key=file_key,
            node_id=root_node_id,
            output_dir=output_dir,
            force_sync=force_sync,
            naming_filters=naming_filters
        )

        # 7. Display results
        print("\n[SUCCESS] Export completed!")
        print(f"[RESULT] Result: {result}")

        # 8. Display created files
        print(f"\n[FILES] Files in {output_dir}:")
        output_path = Path(output_dir)

        if output_path.exists():
            files = list(output_path.rglob("*"))
            files = [f for f in files if f.is_file()]

            if files:
                print(f"   Total files: {len(files)}")

                # Categorize files
                svg_files = [f for f in files if f.suffix == '.svg']
                json_files = [f for f in files if f.suffix == '.json']
                md_files = [f for f in files if f.suffix == '.md']

                print(f"   SVG files: {len(svg_files)}")
                print(f"   JSON metadata: {len(json_files)}")
                print(f"   Markdown reports: {len(md_files)}")

                # Display some SVG files
                if svg_files:
                    print("\n[SVG] Created SVG Files:")
                    for i, svg_file in enumerate(svg_files[:5], 1):  # Show first 5 files
                        size = svg_file.stat().st_size
                        print(f"   {i}. {svg_file.name} ({size} bytes)")

                    if len(svg_files) > 5:
                        print(f"   ... and {len(svg_files) - 5} more files")

                # Display reports
                for report_file in md_files:
                    if 'summary' in report_file.name:
                        print(f"\n[REPORT] Report: {report_file}")
                        try:
                            with open(report_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                print("   Summary content:")
                                lines = content.split('\n')[:10]  # Show first 10 lines
                                for line in lines:
                                    if line.strip():
                                        print(f"   {line}")
                        except Exception as e:
                            print(f"   Cannot read report: {e}")
            else:
                print("   No files created")
        else:
            print(f"   Directory {output_dir} does not exist")

        return True

    except Exception as e:
        print(f"[ERROR] Error running demo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(demo_export_and_show())
    sys.exit(0 if success else 1)