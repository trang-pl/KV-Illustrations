#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Environment Variable Loading with python-dotenv
Kiểm tra việc load .env file bằng thư viện python-dotenv
"""

import os
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_dotenv_loading():
    """Test loading environment variables using python-dotenv"""
    print("[TEST] Testing python-dotenv environment loading")
    print("=" * 50)

    try:
        # Try to import python-dotenv
        from dotenv import load_dotenv
        print("[OK] python-dotenv library is available")

        # Load .env file
        env_path = Path('.env')
        if env_path.exists():
            success = load_dotenv(env_path)
            if success:
                print("[OK] Successfully loaded .env file with python-dotenv")
            else:
                print("[WARN] load_dotenv returned False, but may still have loaded some variables")
        else:
            print("[ERROR] .env file not found")
            return False

        # Check if Figma credentials are loaded
        figma_token = os.getenv('FIGMA_API_TOKEN')
        figma_file_key = os.getenv('FIGMA_FILE_KEY')

        print("\n[CHECK] Environment Variables Check:")
        print("-" * 30)

        if figma_token:
            print(f"[OK] FIGMA_API_TOKEN loaded: {figma_token[:10]}...")
        else:
            print("[ERROR] FIGMA_API_TOKEN not found in environment")

        if figma_file_key:
            print(f"[OK] FIGMA_FILE_KEY loaded: {figma_file_key[:10]}...")
        else:
            print("[ERROR] FIGMA_FILE_KEY not found in environment")

        # Test other important variables
        host = os.getenv('HOST', 'localhost')
        port = os.getenv('PORT', '8022')

        print(f"[INFO] HOST: {host}")
        print(f"[INFO] PORT: {port}")

        return bool(figma_token and figma_file_key)

    except ImportError:
        print("[ERROR] python-dotenv library not installed")
        print("[INFO] Install with: pip install python-dotenv")

        # Fallback: manual .env loading
        print("\n[FALLBACK] Testing manual .env loading")
        print("-" * 30)

        env_path = Path('.env')
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()

                figma_token = os.getenv('FIGMA_API_TOKEN')
                figma_file_key = os.getenv('FIGMA_FILE_KEY')

                if figma_token and figma_file_key:
                    print("[OK] Manual .env loading successful")
                    return True
                else:
                    print("[ERROR] Manual .env loading failed")
                    return False

            except Exception as e:
                print(f"[ERROR] Manual .env loading error: {e}")
                return False
        else:
            print("[ERROR] .env file not found")
            return False

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_dotenv_loading()
    print(f"\n[RESULT] Environment loading test: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)