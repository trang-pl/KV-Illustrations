#!/usr/bin/env python3
"""
Simple test to check Figma API connection
"""

import asyncio
import aiohttp
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

import dotenv
dotenv.load_dotenv()

async def test_figma_api():
    """Test basic Figma API connection"""
    token = os.environ.get('FIGMA_API_TOKEN')
    file_key = os.environ.get('FIGMA_FILE_KEY')

    if not token:
        print("ERROR: FIGMA_API_TOKEN not found")
        return

    if not file_key:
        print("ERROR: FIGMA_FILE_KEY not found")
        return

    print(f"Token: {token[:10]}...{token[-5:]}")
    print(f"File Key: {file_key}")

    headers = {"X-Figma-Token": token, "Content-Type": "application/json"}
    url = f"https://api.figma.com/v1/files/{file_key}"

    async with aiohttp.ClientSession() as session:
        try:
            print(f"Calling: {url}")
            async with session.get(url, headers=headers) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    print("SUCCESS: API call successful!")
                    print(f"File name: {data.get('name', 'Unknown')}")
                    print(f"Last modified: {data.get('lastModified', 'Unknown')}")
                    print(f"Thumbnail: {data.get('thumbnailUrl', 'Unknown')}")
                else:
                    error_text = await response.text()
                    print(f"FAILED: API call failed: {error_text}")

        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_figma_api())