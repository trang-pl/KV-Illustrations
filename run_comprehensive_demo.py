#!/usr/bin/env python3
"""
Demo Runner cho Comprehensive Figma SVG Export Test
Chạy test comprehensive để demo cả prefix mode và node ID mode
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def run_demo():
    """Run comprehensive demo"""
    print("🚀 Starting Comprehensive Figma SVG Export Demo")
    print("=" * 60)

    try:
        # Import và chạy comprehensive demo
        from test.test_comprehensive_demo import run_comprehensive_demo

        results = await run_comprehensive_demo()

        if "error" in results:
            print(f"\n❌ Demo failed: {results['error']}")
            return False
        else:
            print("\n✅ Demo completed successfully!")
            print(f"📊 Total exported: {results['total_exported']}")
            print(f"⏱️  Total time: {results['total_time']:.2f}s")
            print(f"🏆 Winner: {results['winner']}")
            print(f"📁 Output: {results['output_directory']}")
            return True

    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    try:
        success = asyncio.run(run_demo())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()