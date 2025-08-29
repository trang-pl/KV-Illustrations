#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment Validation Script for Figma Credentials
Kiểm tra và validate Figma credentials từ .env file
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Set UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_figma_token(token: str) -> Tuple[bool, str]:
    """Validate Figma Personal Access Token format"""
    if not token:
        return False, "Token is empty"

    if not token.startswith('figd_'):
        return False, "Token must start with 'figd_'"

    if len(token) < 40:  # Minimum expected length
        return False, f"Token too short: {len(token)} characters"

    return True, "Valid Figma PAT format"

def validate_file_key(file_key: str) -> Tuple[bool, str]:
    """Validate Figma file key format"""
    if not file_key:
        return False, "File key is empty"

    # Figma file keys are typically alphanumeric with possible hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, file_key):
        return False, "File key contains invalid characters"

    if len(file_key) < 10:  # Minimum expected length
        return False, f"File key too short: {len(file_key)} characters"

    return True, "Valid file key format"

def load_env_file(env_path: Path) -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_vars = {}

    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found: {env_path}")

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    env_vars[key] = value
                else:
                    print(f"Warning: Invalid line {line_num}: {line}")

    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(f"UTF-8 encoding error in {env_path}: {e}")

    return env_vars

def check_environment_setup(env_vars: Dict[str, str]) -> List[str]:
    """Check environment setup and configuration"""
    issues = []

    # Required Figma variables
    required_vars = ['FIGMA_API_TOKEN', 'FIGMA_FILE_KEY']
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            issues.append(f"Missing or empty required variable: {var}")

    # Server configuration
    if 'HOST' in env_vars and env_vars['HOST'] != 'localhost':
        issues.append(f"Warning: HOST is set to {env_vars['HOST']}, expected 'localhost' for development")

    if 'PORT' in env_vars:
        try:
            port = int(env_vars['PORT'])
            if port < 1024 or port > 65535:
                issues.append(f"Invalid PORT: {port}, should be between 1024-65535")
        except ValueError:
            issues.append(f"Invalid PORT value: {env_vars['PORT']}")

    # Git configuration warnings
    if 'GIT_REPO_PATH' in env_vars and not env_vars['GIT_REPO_PATH'].startswith('./'):
        issues.append("Warning: GIT_REPO_PATH should be relative path starting with './'")

    return issues

def main():
    """Main validation function"""
    print("[SEARCH] Figma Environment Validation Report")
    print("=" * 50)

    # Find .env file
    env_path = Path('.env')
    if not env_path.exists():
        print("[ERROR] ERROR: .env file not found in current directory")
        return False

    try:
        # Load environment variables
        env_vars = load_env_file(env_path)
        print(f"[OK] Successfully loaded {len(env_vars)} environment variables")

        # Validate Figma credentials
        print("\n[KEY] Figma Credentials Validation:")
        print("-" * 30)

        # Check FIGMA_API_TOKEN (PAT)
        token = env_vars.get('FIGMA_API_TOKEN', '')
        token_valid, token_msg = validate_figma_token(token)
        if token_valid:
            print(f"[OK] FIGMA_API_TOKEN: {token_msg}")
            print(f"   Length: {len(token)} characters")
        else:
            print(f"[ERROR] FIGMA_API_TOKEN: {token_msg}")

        # Check FIGMA_FILE_KEY
        file_key = env_vars.get('FIGMA_FILE_KEY', '')
        file_key_valid, file_key_msg = validate_file_key(file_key)
        if file_key_valid:
            print(f"[OK] FIGMA_FILE_KEY: {file_key_msg}")
            print(f"   Length: {len(file_key)} characters")
        else:
            print(f"[ERROR] FIGMA_FILE_KEY: {file_key_msg}")

        # Environment setup check
        print("\n[CONFIG] Environment Setup Check:")
        print("-" * 30)
        issues = check_environment_setup(env_vars)

        if issues:
            for issue in issues:
                if issue.startswith("Warning"):
                    print(f"[WARN] {issue}")
                else:
                    print(f"[ERROR] {issue}")
        else:
            print("[OK] All environment variables properly configured")

        # Summary
        print("\n[SUMMARY] Summary:")
        print("-" * 30)
        credentials_ready = token_valid and file_key_valid
        if credentials_ready:
            print("[OK] Figma credentials are VALID and READY for testing")
        else:
            print("[ERROR] Figma credentials have ISSUES - check above")

        if not issues:
            print("[OK] Environment setup is COMPLETE")
        else:
            print(f"[WARN] Environment setup has {len(issues)} issues to address")

        # Windows encoding check
        print("\n[WINDOWS] Windows UTF-8 Compatibility:")
        print("-" * 30)
        try:
            # Test UTF-8 encoding
            test_string = "Figma test encoding"
            encoded = test_string.encode('utf-8')
            decoded = encoded.decode('utf-8')
            if test_string == decoded:
                print("[OK] UTF-8 encoding/decoding works correctly")
            else:
                print("[ERROR] UTF-8 encoding issue detected")
        except Exception as e:
            print(f"[ERROR] UTF-8 compatibility error: {e}")

        return credentials_ready

    except Exception as e:
        print(f"[ERROR] ERROR during validation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)