#!/usr/bin/env python3
"""
Credentials Loader Module v1.0
==============================

Load và validate Figma credentials từ environment variables và config file.

Features:
- Load .env file
- Validate Figma API token format
- Test API connectivity
- Environment-specific configuration
- Credential security và masking

Author: DS Tools - Modular Pipeline
Version: 1.0.0
Date: 2025-08-29
"""

import os
import sys
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Fix Windows encoding issues - SAFER APPROACH
if sys.platform == "win32":
    try:
        import codecs
        # Only apply if not already applied and buffer exists
        if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, 'reconfigure'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer') and not hasattr(sys.stderr, 'reconfigure'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, OSError):
        # If encoding fix fails, continue without it
        pass

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import dotenv

class CredentialsLoader:
    """Load và validate Figma credentials với comprehensive testing"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "scripts/config/pipeline_config.json"
        # Adjust path if running from modules directory
        if not Path(self.config_path).exists():
            self.config_path = "../config/pipeline_config.json"
        self.credentials = {}
        self.validation_results = {}
        self.start_time = None
        self.end_time = None

    async def load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration từ JSON file"""
        print("[CONFIG] Loading pipeline configuration...")

        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print("[SUCCESS] Configuration loaded successfully")
        return config

    async def load_environment_variables(self) -> Dict[str, str]:
        """Load environment variables từ .env file"""
        print("[ENV] Loading environment variables...")

        # Load .env file
        dotenv.load_dotenv()

        env_vars = {
            'FIGMA_API_TOKEN': os.getenv('FIGMA_API_TOKEN', ''),
            'FIGMA_FILE_KEY': os.getenv('FIGMA_FILE_KEY', ''),
            'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development')
        }

        print("[SUCCESS] Environment variables loaded")
        return env_vars

    def validate_token_format(self, token: str) -> Dict[str, Any]:
        """Validate Figma API token format"""
        print("[VALIDATION] Validating token format...")

        validation = {
            "valid": False,
            "format_correct": False,
            "length_valid": False,
            "prefix_valid": False,
            "errors": []
        }

        if not token:
            validation["errors"].append("Token is empty")
            return validation

        # Check length (Figma tokens are typically long)
        if len(token) < 20:
            validation["errors"].append("Token too short")
        else:
            validation["length_valid"] = True

        # Check prefix (Figma tokens start with 'figd_')
        if token.startswith('figd_'):
            validation["prefix_valid"] = True
        else:
            validation["errors"].append("Invalid token prefix (should start with 'figd_')")

        # Check for basic format
        if len(token) >= 20 and token.startswith('figd_'):
            validation["format_correct"] = True

        # Overall validation
        if validation["format_correct"] and validation["length_valid"] and validation["prefix_valid"]:
            validation["valid"] = True

        if validation["valid"]:
            print("[SUCCESS] Token format is valid")
        else:
            print("[ERROR] Token format is invalid")
            for error in validation["errors"]:
                print(f"   - {error}")

        return validation

    def validate_file_key_format(self, file_key: str) -> Dict[str, Any]:
        """Validate Figma file key format"""
        print("[VALIDATION] Validating file key format...")

        validation = {
            "valid": False,
            "format_correct": False,
            "length_valid": False,
            "errors": []
        }

        if not file_key:
            validation["errors"].append("File key is empty")
            return validation

        # Check length (Figma file keys are typically around 22 characters)
        if len(file_key) < 10:
            validation["errors"].append("File key too short")
        elif len(file_key) > 50:
            validation["errors"].append("File key too long")
        else:
            validation["length_valid"] = True

        # Check for valid characters (alphanumeric)
        if file_key.replace('-', '').replace('_', '').isalnum():
            validation["format_correct"] = True
        else:
            validation["errors"].append("Invalid characters in file key")

        # Overall validation
        if validation["format_correct"] and validation["length_valid"]:
            validation["valid"] = True

        if validation["valid"]:
            print("[SUCCESS] File key format is valid")
        else:
            print("[ERROR] File key format is invalid")
            for error in validation["errors"]:
                print(f"   - {error}")

        return validation

    async def test_api_connectivity(self, token: str, file_key: str) -> Dict[str, Any]:
        """Test Figma API connectivity"""
        print("[CONNECTIVITY] Testing Figma API connectivity...")

        test_result = {
            "success": False,
            "response_time": None,
            "status_code": None,
            "error": None,
            "file_accessible": False
        }

        try:
            # Test API endpoint
            url = f"https://api.figma.com/v1/files/{file_key}"
            headers = {
                "X-Figma-Token": token,
                "User-Agent": "Figma-Pipeline-Credentials-Loader/1.0"
            }

            start_time = asyncio.get_event_loop().time()

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    end_time = asyncio.get_event_loop().time()
                    test_result["response_time"] = end_time - start_time
                    test_result["status_code"] = response.status

                    if response.status == 200:
                        test_result["success"] = True
                        test_result["file_accessible"] = True
                        print("[SUCCESS] API connectivity test passed")
                        print(f"🌐 [CONNECTIVITY] Response time: {test_result['response_time']:.2f} seconds")
                    else:
                        error_text = await response.text()
                        test_result["error"] = f"HTTP {response.status}: {error_text}"
                        print(f"[ERROR] API test failed: {test_result['error']}")

        except asyncio.TimeoutError:
            test_result["error"] = "Request timeout"
            print("[ERROR] API test failed: Request timeout")
        except aiohttp.ClientError as e:
            test_result["error"] = f"Network error: {str(e)}"
            print(f"[ERROR] API test failed: {test_result['error']}")
        except Exception as e:
            test_result["error"] = f"Unexpected error: {str(e)}"
            print(f"[ERROR] API test failed: {test_result['error']}")

        return test_result

    def mask_sensitive_data(self, data: str, visible_chars: int = 4) -> str:
        """Mask sensitive data for logging"""
        if len(data) <= visible_chars * 2:
            return "*" * len(data)
        return data[:visible_chars] + "*" * (len(data) - visible_chars * 2) + data[-visible_chars:]

    async def load_and_validate_credentials(self) -> Dict[str, Any]:
        """Main method to load và validate all credentials"""
        print("\n[CREDENTIALS] Starting credentials loading và validation")
        print("=" * 80)

        self.start_time = asyncio.get_event_loop().time()

        try:
            # Load configuration
            config = await self.load_config()
            figma_config = config.get("figma", {})

            # Load environment variables
            env_vars = await self.load_environment_variables()

            # Prioritize environment variables over config
            api_token = env_vars.get('FIGMA_API_TOKEN') or figma_config.get('api_token', '')
            file_key = env_vars.get('FIGMA_FILE_KEY') or figma_config.get('file_key', '')

            print(f"[CREDENTIALS] API Token: {self.mask_sensitive_data(api_token)}")
            print(f"[CREDENTIALS] File Key: {file_key}")

            # Validate credentials
            token_validation = self.validate_token_format(api_token)
            file_key_validation = self.validate_file_key_format(file_key)

            # Test API connectivity if validations pass
            connectivity_test = None
            if token_validation["valid"] and file_key_validation["valid"]:
                connectivity_test = await self.test_api_connectivity(api_token, file_key)

            # Compile results
            credentials_result = {
                "success": False,
                "credentials": {
                    "api_token": api_token,
                    "file_key": file_key,
                    "environment": env_vars.get('ENVIRONMENT', 'development')
                },
                "validation": {
                    "token": token_validation,
                    "file_key": file_key_validation
                },
                "connectivity": connectivity_test,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "masked_token": self.mask_sensitive_data(api_token)
            }

            # Determine overall success
            validation_success = token_validation["valid"] and file_key_validation["valid"]
            connectivity_success = connectivity_test and connectivity_test["success"]

            if validation_success and connectivity_success:
                credentials_result["success"] = True
                print("\n[SUCCESS] All validations passed successfully!")
            elif validation_success:
                print("\n[WARNING] Format validation passed but connectivity test failed")
            else:
                print("\n[ERROR] Credential validation failed")

            self.end_time = asyncio.get_event_loop().time()
            credentials_result["processing_time"] = self.end_time - self.start_time

            return credentials_result

        except Exception as e:
            self.end_time = asyncio.get_event_loop().time()
            print(f"\n[ERROR] Credentials loading failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time": self.end_time - self.start_time if self.start_time else 0
            }

    async def save_validation_report(self, result: Dict[str, Any], output_dir: str = "exports/credentials_loader/"):
        """Save validation report to file"""
        print("[REPORT] Saving credentials validation report...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save detailed report
        report_file = output_path / "credentials_validation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Save summary report
        summary_file = output_path / "credentials_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Credentials Validation Summary\n\n")
            f.write(f"**Timestamp:** {result.get('timestamp', 'N/A')}\n\n")
            f.write(f"**Status:** {'✅ SUCCESS' if result.get('success') else '❌ FAILED'}\n\n")

            if result.get('success'):
                f.write("## Credentials Loaded\n\n")
                f.write(f"- **API Token:** {result.get('masked_token', 'N/A')}\n")
                f.write(f"- **File Key:** {result['credentials'].get('file_key', 'N/A')}\n")
                f.write(f"- **Environment:** {result['credentials'].get('environment', 'N/A')}\n\n")

                if result.get('connectivity'):
                    conn = result['connectivity']
                    f.write("## API Connectivity\n\n")
                    f.write(f"- **Status:** {'✅ Connected' if conn.get('success') else '❌ Failed'}\n")
                    if conn.get('response_time'):
                        f.write(f"- **Response Time:** {conn['response_time']:.2f} seconds\n")
                    if conn.get('file_accessible'):
                        f.write("- **File Access:** ✅ Accessible\n")
            else:
                f.write("## Error\n\n")
                f.write(f"**Error:** {result.get('error', 'Unknown error')}\n\n")

            f.write(f"**Processing Time:** {result.get('processing_time', 0):.2f} seconds\n")

        print(f"✅ [REPORT] Reports saved to: {output_path}")
        return str(report_file), str(summary_file)

async def main():
    """Main function for standalone execution"""
    print("CREDENTIALS LOADER MODULE v1.0")
    print("=" * 80)
    print("Loading và validating Figma credentials")
    print()

    loader = CredentialsLoader()

    try:
        # Load và validate credentials
        result = await loader.load_and_validate_credentials()

        # Save reports
        await loader.save_validation_report(result)

        # Final summary
        print("\n" + "=" * 80)
        print("🎯 CREDENTIALS LOADER SUMMARY")
        print("=" * 80)

        if result.get('success'):
            print("Status: SUCCESS")
            print(f"🔑 API Token: {result.get('masked_token', 'N/A')}")
            print(f"📁 File Key: {result['credentials'].get('file_key', 'N/A')}")
            if result.get('connectivity', {}).get('success'):
                print("API Connectivity: Connected")
        else:
            print("Status: FAILED")
            print(f"📊 Error: {result.get('error', 'Unknown error')}")

        return result.get('success', False)

    except Exception as e:
        print(f"\n❌ [FATAL] Credentials loader failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n🏁 Credentials loader {'completed successfully' if success else 'failed'}")

    sys.exit(0 if success else 1)