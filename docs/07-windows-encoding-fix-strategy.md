# Windows Encoding Fix Strategy
**Document Version:** 1.0
**Date:** 2025-08-29
**Author:** DS Tools - Architect Mode

## Problem Statement

### Critical Issue: 'charmap' Codec Error

**Error Message:**
```
'charmap' codec can't encode characters in position 0-1: character maps to <undefined>
```

**Impact:** Complete system failure on Windows platforms, blocking production deployment.

**Root Cause:** Windows console (cmd.exe) has limited Unicode support and defaults to 'cp1252' or 'charmap' encoding, which cannot handle Unicode characters used in the application.

## Solution Architecture

### 1. Multi-Layer Encoding Strategy

#### Layer 1: System-Level Configuration
```python
# windows_encoding_fix.py
import sys
import os
import locale

def configure_windows_encoding():
    """Configure Windows system for UTF-8 encoding"""

    # Force UTF-8 encoding for stdout/stderr
    if sys.platform == "win32":
        # Set console output encoding
        os.environ['PYTHONIOENCODING'] = 'utf-8'

        # Reconfigure stdout/stderr for UTF-8
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except AttributeError:
            # Python < 3.7 fallback
            pass

        # Set locale to UTF-8 if available
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except locale.Error:
                pass
```

#### Layer 2: Safe Unicode Operations

```python
class SafeUnicodeHandler:
    """Handle Unicode operations safely across platforms"""

    @staticmethod
    def safe_print(text: str, *args, **kwargs):
        """Print text safely, handling encoding errors"""
        try:
            print(text, *args, **kwargs)
        except UnicodeEncodeError:
            # Fallback: encode and decode with error handling
            safe_text = text.encode('utf-8', errors='replace').decode('utf-8')
            print(safe_text, *args, **kwargs)

    @staticmethod
    def safe_file_write(filepath: str, content: str, encoding: str = 'utf-8'):
        """Write to file with encoding error handling"""
        try:
            with open(filepath, 'w', encoding=encoding) as f:
                f.write(content)
        except UnicodeEncodeError:
            # Fallback: use error replacement
            safe_content = content.encode(encoding, errors='replace').decode(encoding)
            with open(filepath, 'w', encoding=encoding) as f:
                f.write(safe_content)

    @staticmethod
    def safe_json_dump(data: dict, filepath: str):
        """Dump JSON data safely"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except UnicodeEncodeError:
            # Fallback: escape non-ASCII characters
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=True)
```

#### Layer 3: Application-Specific Fixes

```python
class EncodingSafeExporter:
    """Enhanced Figma Exporter with encoding safety"""

    def __init__(self, *args, **kwargs):
        # Initialize encoding fixes first
        configure_windows_encoding()

        # Replace standard print with safe version
        self.safe_print = SafeUnicodeHandler.safe_print

        # Continue with normal initialization
        super().__init__(*args, **kwargs)

    def export_nodes(self, nodes_data, file_version):
        """Export with encoding-safe operations"""

        self.safe_print(f"🚀 Starting export with type: {self.export_config.export_type}")

        # All print statements use safe_print
        # All file operations use safe methods

        # ... rest of export logic
```

### 2. GitHub Integration Encoding Safety

#### Base64 Encoding Fix
```python
def safe_base64_encode(content: bytes) -> str:
    """Safely encode content to base64"""
    try:
        return base64.b64encode(content).decode('utf-8')
    except UnicodeDecodeError:
        # Handle binary content that can't be decoded as UTF-8
        return base64.b64encode(content).decode('latin-1')
```

#### File Upload Safety
```python
def safe_file_upload(self, local_path: Path, repo_path: str) -> bool:
    """Upload file with encoding safety"""
    try:
        with open(local_path, 'rb') as f:
            file_content = f.read()

        # Safe base64 encoding
        encoded_content = safe_base64_encode(file_content)

        # GitHub API request with proper headers
        headers = {
            'Authorization': f'Bearer {self.github_pat}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
        }

        data = {
            'message': commit_message,
            'content': encoded_content
        }

        response = requests.put(url, headers=headers, json=data)
        return response.status_code in [200, 201]

    except Exception as e:
        self.safe_print(f"❌ Upload failed: {str(e)}")
        return False
```

## Implementation Plan

### Phase 1: Core Encoding Infrastructure (Day 1-2)

#### 1.1 Create Encoding Utilities Module
**File:** `utils/encoding_utils.py`
- `configure_windows_encoding()`
- `SafeUnicodeHandler` class
- Platform detection utilities

#### 1.2 Update Main Exporter
**File:** `scripts/01-figma-enhanced-svg-exporter-v2.0.py`
- Import encoding utilities
- Initialize encoding configuration
- Replace print statements with safe_print
- Update file operations

#### 1.3 Fix GitHub Integration
**File:** `scripts/01-figma-enhanced-svg-exporter-v2.0.py`
- Update `GitHubPushService.upload_file()`
- Implement safe base64 encoding
- Add error handling for encoding failures

### Phase 2: Comprehensive Testing (Day 3)

#### 2.1 Create Encoding Test Suite
**File:** `test/test_windows_encoding.py`
- Test Unicode character handling
- Test file operations with special characters
- Test GitHub integration encoding
- Cross-platform validation

#### 2.2 Update Existing Tests
**File:** `test/test_naming_prefix_v2.0.py`
- Add encoding-safe test runner
- Validate Windows compatibility
- Test with Unicode content

### Phase 3: Production Validation (Day 4-5)

#### 3.1 Environment Validation
**File:** `scripts/validate_environment.py`
- Check system encoding capabilities
- Validate Python configuration
- Test file system encoding support

#### 3.2 CI/CD Integration
**File:** `.github/workflows/test-encoding.yml`
- Windows-specific test jobs
- Encoding validation steps
- Cross-platform test matrix

## Testing Strategy

### 1. Unit Tests
```python
def test_unicode_print():
    """Test safe Unicode printing"""
    test_strings = [
        "Normal ASCII text",
        "Unicode: 🚀 ✅ ❌",
        "Vietnamese: Tiếng Việt với encoding",
        "Emoji: 😀 🎉 🔥",
    ]

    for test_str in test_strings:
        # Should not raise UnicodeEncodeError
        safe_print(test_str)
        assert True  # If we get here, test passed
```

### 2. Integration Tests
```python
def test_file_operations():
    """Test file operations with Unicode content"""
    test_content = {
        "vietnamese": "Tiếng Việt encoding test",
        "emoji": "🚀 Test with emoji 🔥",
        "special": "Special chars: äöü ñ é è",
    }

    for name, content in test_content.items():
        filepath = f"test_{name}.txt"
        safe_file_write(filepath, content)

        # Verify content was written correctly
        with open(filepath, 'r', encoding='utf-8') as f:
            read_content = f.read()
            assert read_content == content
```

### 3. End-to-End Tests
```python
def test_full_export_pipeline():
    """Test complete export with Unicode content"""
    # Create test data with Unicode names
    test_nodes = [
        {
            "id": "1:1",
            "name": "svg_exporter_icon_🚀",
            "type": "COMPONENT"
        },
        {
            "id": "1:2",
            "name": "svg_exporter_text_viết",
            "type": "COMPONENT"
        }
    ]

    # Should complete without encoding errors
    exporter = EncodingSafeExporter(export_config)
    result = exporter.export_nodes(test_nodes, "encoding-test-v1.0")

    assert result["processed_nodes"] == len(test_nodes)
```

## Monitoring & Error Handling

### 1. Encoding Error Tracking
```python
class EncodingMonitor:
    """Monitor encoding-related errors"""

    def __init__(self):
        self.encoding_errors = []
        self.fallbacks_used = []

    def log_encoding_error(self, operation: str, error: Exception):
        """Log encoding error for analysis"""
        error_info = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "platform": sys.platform,
        }
        self.encoding_errors.append(error_info)

    def log_fallback_used(self, operation: str, fallback: str):
        """Log when fallback encoding was used"""
        fallback_info = {
            "operation": operation,
            "fallback": fallback,
            "timestamp": datetime.now().isoformat(),
        }
        self.fallbacks_used.append(fallback_info)
```

### 2. Error Recovery Strategies
```python
def graceful_encoding_failure(operation: str, error: Exception):
    """Handle encoding failures gracefully"""

    # Log the error
    encoding_monitor.log_encoding_error(operation, error)

    # Attempt recovery strategies
    if operation == "print":
        # Fallback to ASCII-safe output
        safe_print(f"[ENCODING ERROR] {operation}: Using safe output")
    elif operation == "file_write":
        # Use ensure_ascii=True for JSON
        safe_json_dump(data, filepath)
    elif operation == "github_upload":
        # Skip upload with warning
        safe_print("⚠️ GitHub upload skipped due to encoding issues")

    # Continue execution
    return True
```

## Deployment Checklist

### Pre-Deployment Validation
- [ ] Windows encoding configuration tested
- [ ] Unicode content handling validated
- [ ] File operations with special characters tested
- [ ] GitHub integration encoding verified
- [ ] Cross-platform compatibility confirmed

### Production Monitoring
- [ ] Encoding error tracking enabled
- [ ] Fallback usage monitoring active
- [ ] Performance impact of encoding fixes measured
- [ ] User-reported encoding issues tracking

### Rollback Plan
- [ ] Original code backup available
- [ ] Feature flags for encoding fixes
- [ ] Gradual rollout strategy
- [ ] Quick rollback procedures documented

## Success Metrics

### Technical Metrics
- **Encoding Error Rate:** Target < 0.1%
- **Fallback Usage:** Target < 1% of operations
- **Performance Impact:** Target < 5% degradation
- **Cross-Platform Success:** Target 100% compatibility

### Business Metrics
- **Deployment Success:** Windows production deployment successful
- **User Satisfaction:** No encoding-related user complaints
- **System Reliability:** No encoding-related system failures

## Conclusion

This comprehensive encoding fix strategy addresses the critical Windows compatibility issue while maintaining system performance and reliability. The multi-layer approach ensures robust Unicode handling across all operations while providing graceful fallbacks for edge cases.

**Implementation Priority:** URGENT - Critical blocker for production deployment
**Estimated Effort:** 5 days for complete implementation and testing
**Risk Level:** Low - Well-established encoding patterns and comprehensive testing

---

**Document Version:** 1.0
**Last Updated:** 2025-08-29
**Review Status:** Ready for implementation