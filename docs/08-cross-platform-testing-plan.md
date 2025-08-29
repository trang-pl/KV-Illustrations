# Cross-Platform Testing Plan for Enhanced Figma SVG Exporter v2.0
**Document Version:** 1.0
**Date:** 2025-08-29
**Author:** DS Tools - Architect Mode

## Overview

### Objective
Establish comprehensive cross-platform compatibility testing to ensure the Enhanced Figma SVG Exporter v2.0 works reliably across all supported platforms, with special focus on resolving Windows encoding issues.

### Scope
- **Platforms:** Windows, macOS, Linux
- **Python Versions:** 3.8, 3.9, 3.10, 3.11
- **Key Focus Areas:** Encoding, file operations, GitHub integration, naming prefix logic

## Test Environment Matrix

### Primary Test Environments

| Platform | Version | Python | Architecture | Priority |
|----------|---------|--------|--------------|----------|
| Windows | 10 Pro (22H2) | 3.8, 3.9, 3.10, 3.11 | x64 | Critical |
| Windows | 11 Pro (23H2) | 3.9, 3.10, 3.11 | x64 | High |
| Ubuntu | 20.04 LTS | 3.8, 3.9, 3.10 | x64 | High |
| Ubuntu | 22.04 LTS | 3.10, 3.11 | x64 | Medium |
| macOS | 12.0 Monterey | 3.8, 3.9, 3.10 | x64/ARM | Medium |
| macOS | 13.0 Ventura | 3.9, 3.10, 3.11 | x64/ARM | Medium |

### Secondary Test Environments

| Platform | Version | Python | Purpose |
|----------|---------|--------|---------|
| Windows Server | 2022 | 3.9, 3.10 | Server deployment |
| CentOS | 7, 8 | 3.8, 3.9 | Enterprise Linux |
| Fedora | 37, 38 | 3.10, 3.11 | Bleeding edge |

## Test Categories

### 1. Encoding & Unicode Tests

#### 1.1 Terminal Output Tests
```python
# test_encoding_terminal.py
def test_unicode_terminal_output():
    """Test Unicode characters in terminal output"""
    test_cases = [
        "ASCII: Hello World",
        "Emoji: 🚀 ✅ ❌ 🔥",
        "Vietnamese: Tiếng Việt encoding test",
        "Special: äöü ñ é è ç",
        "Symbols: © ® ™ € £ ¥",
        "Math: α β γ δ ∑ ∫ √",
    ]

    for test_case in test_cases:
        # Should not raise UnicodeEncodeError
        safe_print(f"Testing: {test_case}")
        assert_terminal_output_successful()
```

#### 1.2 File Operations Tests
```python
# test_encoding_files.py
def test_unicode_file_operations():
    """Test file operations with Unicode content"""

    test_files = {
        "vietnamese.txt": "Nội dung tiếng Việt với encoding UTF-8",
        "emoji.txt": "🚀 Test emoji content 🔥",
        "special_chars.txt": "Spécial caractères: äöü ñ é è",
        "mixed.json": {
            "vietnamese": "Tiếng Việt",
            "emoji": "😀 🎉",
            "special": "café résumé"
        }
    }

    for filename, content in test_files.items():
        # Test write operations
        safe_file_write(filename, content)

        # Test read operations
        read_content = safe_file_read(filename)
        assert read_content == content

        # Test JSON operations
        if filename.endswith('.json'):
            safe_json_dump(content, filename)
            loaded_content = safe_json_load(filename)
            assert loaded_content == content
```

#### 1.3 File Path Tests
```python
# test_encoding_paths.py
def test_unicode_file_paths():
    """Test file operations with Unicode in paths"""

    base_path = Path("test_unicode_paths")

    test_paths = [
        "tiếng_việt_folder/file.txt",
        "emoji_🚀_folder/🚀_file.txt",
        "spécial_chars/café_file.txt",
        "mixed_αβγ/∑∫√_file.txt"
    ]

    for test_path in test_paths:
        full_path = base_path / test_path

        # Create directory structure
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Test file creation
        safe_file_write(full_path, f"Content for {test_path}")

        # Test file reading
        content = safe_file_read(full_path)
        assert f"Content for {test_path}" in content
```

### 2. Naming Prefix Logic Tests

#### 2.1 Core Logic Validation
```python
# test_naming_prefix_cross_platform.py
def test_naming_prefix_logic():
    """Test naming prefix logic across platforms"""

    test_cases = [
        # (input_name, expected_output, export_type)
        ("svg_exporter_button_primary", "button_primary", "svg_exporter_test"),
        ("img_exporter_hero_banner", "hero_banner", "img_exporter_test"),
        ("svg_exporter_icon_🚀", "icon_🚀", "svg_exporter_test"),
        ("img_exporter_café", "café", "img_exporter_test"),
    ]

    for input_name, expected_output, export_type in test_cases:
        config = {"export_type": export_type}
        processor = ExportCriteriaProcessor(config)

        export_name = processor.get_export_name({"name": input_name})
        assert export_name == expected_output
```

#### 2.2 Duplicate Handling Tests
```python
def test_duplicate_handling_unicode():
    """Test duplicate handling with Unicode names"""

    config = {"export_type": "svg_exporter_test", "duplicate_handling": "rename"}
    processor = ExportCriteriaProcessor(config)

    # Test with Unicode duplicates
    test_names = [
        "svg_exporter_café",
        "svg_exporter_café",  # duplicate
        "svg_exporter_café",  # duplicate
        "svg_exporter_🚀",
        "svg_exporter_🚀",    # duplicate
    ]

    expected_outputs = [
        "café",
        "café_1",
        "café_2",
        "🚀",
        "🚀_1"
    ]

    for i, name in enumerate(test_names):
        export_name = processor.get_export_name({"name": name})
        assert export_name == expected_outputs[i]
```

### 3. GitHub Integration Tests

#### 3.1 Authentication Tests
```python
# test_github_encoding.py
def test_github_auth_encoding():
    """Test GitHub authentication with Unicode credentials"""

    # Test with Unicode in tokens (if applicable)
    # Test with Unicode in repository names
    # Test with Unicode in commit messages

    test_scenarios = [
        {"repo_name": "test-repo", "commit_msg": "Normal commit"},
        {"repo_name": "tiếng-việt-repo", "commit_msg": "Commit tiếng Việt"},
        {"repo_name": "emoji-repo", "commit_msg": "🚀 New features"},
        {"repo_name": "spécial-repo", "commit_msg": "Café update"},
    ]

    for scenario in test_scenarios:
        # Test GitHub service initialization
        service = GitHubPushService(token, "test-owner", scenario["repo_name"])

        # Test commit message encoding
        assert_commit_message_safe(scenario["commit_msg"])
```

#### 3.2 File Upload Tests
```python
def test_github_file_upload_encoding():
    """Test file upload with various content types"""

    test_files = [
        ("ascii.txt", "Simple ASCII content"),
        ("unicode.txt", "Unicode: 🚀 Tiếng Việt café"),
        ("binary.dat", b"\x00\x01\x02\x03\xff\xfe"),  # Binary data
        ("mixed.json", {"unicode": "🚀", "vietnamese": "Tiếng Việt"}),
    ]

    for filename, content in test_files:
        # Create test file
        if isinstance(content, str):
            safe_file_write(filename, content)
        else:
            with open(filename, 'wb') as f:
                f.write(content)

        # Test upload
        success = github_service.upload_file(
            Path(filename),
            f"test-uploads/{filename}",
            f"Upload test: {filename}"
        )

        assert success, f"Failed to upload {filename}"
```

### 4. Performance & Resource Tests

#### 4.1 Memory Usage Tests
```python
# test_performance_encoding.py
def test_memory_usage_unicode():
    """Test memory usage with Unicode content"""

    # Create large Unicode content
    large_unicode_content = "🚀 " * 10000 + "Tiếng Việt " * 5000

    # Measure memory before
    memory_before = get_memory_usage()

    # Process Unicode content
    result = process_unicode_content(large_unicode_content)

    # Measure memory after
    memory_after = get_memory_usage()

    # Assert memory usage is reasonable
    memory_delta = memory_after - memory_before
    assert memory_delta < 50 * 1024 * 1024  # Less than 50MB increase
```

#### 4.2 Processing Speed Tests
```python
def test_processing_speed_unicode():
    """Test processing speed with Unicode content"""

    test_sizes = [100, 1000, 10000]

    for size in test_sizes:
        # Create test data
        unicode_nodes = create_unicode_test_nodes(size)

        # Measure processing time
        start_time = time.time()
        result = exporter.export_nodes(unicode_nodes, f"speed-test-{size}")
        end_time = time.time()

        processing_time = end_time - start_time

        # Assert reasonable processing time (adjust thresholds per platform)
        if sys.platform == "win32":
            assert processing_time < size * 0.01  # 10ms per node on Windows
        else:
            assert processing_time < size * 0.005  # 5ms per node on Unix
```

## Test Automation Framework

### 1. CI/CD Integration

#### GitHub Actions Workflow
```yaml
# .github/workflows/cross-platform-tests.yml
name: Cross-Platform Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-windows:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-test.txt

    - name: Run encoding tests
      run: python -m pytest test/test_encoding_*.py -v

    - name: Run naming prefix tests
      run: python -m pytest test/test_naming_prefix_*.py -v

  test-ubuntu:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    # Similar steps for Ubuntu

  test-macos:
    runs-on: macos-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    # Similar steps for macOS
```

### 2. Local Test Runner

#### Cross-Platform Test Script
```python
# test/run_cross_platform_tests.py
#!/usr/bin/env python3
"""
Cross-platform test runner for Enhanced Figma SVG Exporter
"""

import sys
import platform
import subprocess
from pathlib import Path

def run_platform_specific_tests():
    """Run tests specific to current platform"""

    current_platform = platform.system().lower()

    # Common tests for all platforms
    common_tests = [
        "test/test_naming_prefix_simple.py",
        "test/test_encoding_terminal.py",
        "test/test_encoding_files.py",
    ]

    # Platform-specific tests
    platform_tests = {
        "windows": [
            "test/test_windows_encoding.py",
            "test/test_windows_file_paths.py",
        ],
        "linux": [
            "test/test_linux_encoding.py",
        ],
        "darwin": [
            "test/test_macos_encoding.py",
        ]
    }

    # Run common tests
    for test_file in common_tests:
        if Path(test_file).exists():
            print(f"Running {test_file}...")
            result = subprocess.run([sys.executable, test_file])
            if result.returncode != 0:
                print(f"❌ {test_file} failed")
                return False

    # Run platform-specific tests
    if current_platform in platform_tests:
        for test_file in platform_tests[current_platform]:
            if Path(test_file).exists():
                print(f"Running {test_file}...")
                result = subprocess.run([sys.executable, test_file])
                if result.returncode != 0:
                    print(f"❌ {test_file} failed")
                    return False

    print("✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = run_platform_specific_tests()
    sys.exit(0 if success else 1)
```

## Test Data Management

### 1. Unicode Test Data Repository

#### Test Data Structure
```
test/data/
├── unicode/
│   ├── terminal_output.txt
│   ├── file_content.txt
│   ├── file_paths.txt
│   └── json_content.json
├── figma_nodes/
│   ├── simple_nodes.json
│   ├── unicode_nodes.json
│   └── complex_hierarchy.json
└── github/
    ├── test_repos.txt
    └── commit_messages.txt
```

#### Test Data Generation
```python
# test/generate_unicode_test_data.py
def generate_unicode_test_data():
    """Generate comprehensive Unicode test data"""

    # Terminal output test data
    terminal_data = {
        "emojis": ["🚀", "✅", "❌", "🔥", "😀", "🎉"],
        "languages": {
            "vietnamese": "Tiếng Việt với encoding UTF-8",
            "french": "Français café résumé",
            "german": "Deutsch äöü ß",
            "spanish": "Español ñ é è",
        },
        "symbols": ["©", "®", "™", "€", "£", "¥"],
        "math": ["α", "β", "γ", "δ", "∑", "∫", "√"],
    }

    # Save test data
    safe_json_dump(terminal_data, "test/data/unicode/terminal_output.json")

    # Generate Figma node test data
    unicode_nodes = [
        {"id": "1:1", "name": f"svg_exporter_test_{emoji}", "type": "COMPONENT"}
        for emoji in terminal_data["emojis"]
    ]

    safe_json_dump(unicode_nodes, "test/data/figma_nodes/unicode_nodes.json")
```

## Success Criteria

### 1. Technical Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Pass Rate | ≥ 99% | Automated test results |
| Encoding Error Rate | ≤ 0.1% | Error monitoring |
| Cross-Platform Compatibility | 100% | All platforms supported |
| Performance Impact | ≤ 5% | Benchmark comparisons |

### 2. Platform-Specific Requirements

#### Windows Requirements
- [ ] No 'charmap' codec errors
- [ ] Unicode terminal output works
- [ ] File paths with Unicode characters supported
- [ ] GitHub integration encoding-safe

#### Linux Requirements
- [ ] UTF-8 locale handling
- [ ] Unicode file operations
- [ ] Terminal encoding support
- [ ] Performance optimization

#### macOS Requirements
- [ ] Unicode support for both Intel and Apple Silicon
- [ ] File system encoding compatibility
- [ ] Terminal application compatibility

### 3. Quality Gates

#### Pre-Release Quality Gates
- [ ] All automated tests pass on all platforms
- [ ] Encoding error rate < 0.1%
- [ ] Performance benchmarks met
- [ ] Manual testing completed on primary platforms

#### Release Quality Gates
- [ ] Cross-platform CI/CD pipeline green
- [ ] Production environment validation completed
- [ ] Rollback procedures tested
- [ ] Documentation updated

## Risk Mitigation

### 1. Platform-Specific Risks

#### Windows Encoding Risk
- **Risk:** 'charmap' codec errors in production
- **Mitigation:** Comprehensive encoding fix implementation
- **Testing:** Extensive Windows encoding tests
- **Monitoring:** Encoding error tracking in production

#### macOS Compatibility Risk
- **Risk:** Apple Silicon vs Intel differences
- **Mitigation:** Test on both architectures
- **Testing:** Architecture-specific test suites
- **Monitoring:** Platform detection and optimization

#### Linux Distribution Risk
- **Risk:** Different locale configurations
- **Mitigation:** UTF-8 first approach with fallbacks
- **Testing:** Multiple Linux distribution testing
- **Monitoring:** Locale detection and adaptation

### 2. Performance Risks

#### Unicode Processing Overhead
- **Risk:** Performance degradation with Unicode content
- **Mitigation:** Optimized Unicode handling
- **Testing:** Performance benchmarks with Unicode data
- **Monitoring:** Processing time tracking

#### Memory Usage Increase
- **Risk:** Higher memory usage with Unicode strings
- **Mitigation:** Efficient Unicode string handling
- **Testing:** Memory usage profiling
- **Monitoring:** Memory usage alerts

## Conclusion

This comprehensive cross-platform testing plan ensures the Enhanced Figma SVG Exporter v2.0 works reliably across all supported platforms while maintaining high performance and robust encoding handling.

**Key Success Factors:**
1. **Comprehensive Test Coverage:** All platforms and Python versions tested
2. **Encoding Safety:** Robust Unicode handling with graceful fallbacks
3. **Performance Optimization:** Minimal impact on processing speed
4. **Automated Testing:** CI/CD integration for continuous validation

**Implementation Timeline:** 3-5 days for complete test suite development and validation
**Risk Level:** Low - Established testing patterns and comprehensive coverage

---

**Document Version:** 1.0
**Last Updated:** 2025-08-29
**Next Review:** 2025-09-05 (post-implementation)