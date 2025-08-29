#!/usr/bin/env python3
"""
Test Figma API Token
"""
import os
import aiohttp
import asyncio
from dotenv import load_dotenv

async def test_figma_api():
    # Load environment variables
    load_dotenv()

    api_token = os.getenv('FIGMA_API_TOKEN')
    file_key = os.getenv('FIGMA_FILE_KEY')

    print(f"API Token: {api_token[:10]}...")
    print(f"File Key: {file_key}")

    # Test 1: Check token format
    if not api_token or not api_token.startswith('figd_'):
        print("❌ Invalid token format")
        return False

    # Test 2: Test API connectivity
    headers = {
        "X-Figma-Token": api_token,
        "User-Agent": "Figma-Test/1.0"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # Test with the file
            url = f"https://api.figma.com/v1/files/{file_key}"
            print(f"Testing URL: {url}")

            async with session.get(url) as response:
                print(f"Response status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    print("SUCCESS: API call successful!")
                    print(f"File name: {data.get('name', 'Unknown')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"FAILED: API call failed: {response.status}")
                    print(f"Error: {error_text}")
                    return False

        except Exception as e:
            print(f"ERROR: Network error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_figma_api())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")