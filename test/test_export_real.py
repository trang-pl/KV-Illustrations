#!/usr/bin/env python3
"""
Test Export với FIGMA_FILE_KEY thực tế
Chạy export từ Figma sử dụng file key từ .env
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

async def test_real_export():
    """Test export voi FIGMA_FILE_KEY thuc te tu .env"""
    print("Test Export voi FIGMA_FILE_KEY thuc te")
    print("=" * 60)

    # Lay FIGMA_FILE_KEY tu .env
    file_key = os.environ.get('FIGMA_FILE_KEY')
    if not file_key:
        print("Khong tim thay FIGMA_FILE_KEY trong .env")
        return False

    print(f"File Key: {file_key}")

    # Tao output directory cho test
    output_dir = "./test/exports"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Khoi tao service
    service = FigmaSyncService()

    # Root node ID mac dinh (thuong la "0:1" cho root page)
    root_node_id = "0:1"

    try:
        # Chay sync
        result = await service.process_sync(
            file_key=file_key,
            node_id=root_node_id,
            output_dir=output_dir,
            force_sync=True,  # Force sync de export tat ca
            naming_filters={
                "include_patterns": ["svg_export_*", "icon_*"],
                "exclude_patterns": ["temp_*", "draft_*"],
                "case_sensitive": False
            }
        )

        print("\nTest export hoan thanh!")
        print(f"Ket qua: {result}")

        return True

    except Exception as e:
        print(f"Loi khi chay test export: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_export())
    sys.exit(0 if success else 1)