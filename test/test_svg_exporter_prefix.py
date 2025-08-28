#!/usr/bin/env python3
"""
Test Export theo prefix "svg_exporter_"
Kiểm tra export từ Figma sử dụng file key từ .env với filter prefix cụ thể
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

async def test_svg_exporter_prefix():
    """Test export voi prefix svg_exporter_"""
    print("Test Export theo prefix 'svg_exporter_'")
    print("=" * 60)

    # Lay FIGMA_FILE_KEY tu .env
    file_key = os.environ.get('FIGMA_FILE_KEY')
    if not file_key:
        print("Khong tim thay FIGMA_FILE_KEY trong .env")
        return False

    print(f"File Key: {file_key}")

    # Tao output directory cho test
    output_dir = "./test/exports/svg_exporter_test"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Khoi tao service
    service = FigmaSyncService()

    # Root node ID mac dinh
    root_node_id = "0:1"

    try:
        # Chay sync voi filter prefix svg_exporter_
        result = await service.process_sync(
            file_key=file_key,
            node_id=root_node_id,
            output_dir=output_dir,
            force_sync=True,  # Force sync de export tat ca
            naming_filters={
                "include_patterns": ["svg_exporter_*"],
                "exclude_patterns": ["temp_*", "draft_*"],
                "case_sensitive": False
            }
        )

        print("\nTest export theo prefix 'svg_exporter_' hoan thanh!")
        print(f"Ket qua: {result}")

        # Kiem tra ket qua
        if result.get('exported', 0) > 0:
            print(f"[SUCCESS] Thanh cong: Exported {result['exported']} files voi prefix 'svg_exporter_'")

            # Hien thi danh sach files
            output_path = Path(output_dir)
            if output_path.exists():
                svg_files = list(output_path.rglob("*.svg"))
                if svg_files:
                    print(f"\nFiles duoc export ({len(svg_files)} files):")
                    for i, svg_file in enumerate(svg_files[:10], 1):
                        size = svg_file.stat().st_size
                        print(f"   {i}. {svg_file.name} ({size} bytes)")

                    if len(svg_files) > 10:
                        print(f"   ... va {len(svg_files) - 10} files khac")
        else:
            print("WARNING: Khong co files nao duoc export voi prefix 'svg_exporter_'")
            print("   Co the do:")
            print("   - Khong co nodes nao trong Figma co ten bat dau voi 'svg_exporter_'")
            print("   - File Figma khong ton tai hoac khong duoc chia se")
            print("   - Loi ket noi API")

        return True

    except Exception as e:
        print(f"Loi khi chay test export: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_svg_exporter_prefix())
    sys.exit(0 if success else 1)