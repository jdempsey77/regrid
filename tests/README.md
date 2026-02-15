# Test Harness - Quick Reference

## Running Tests

### All tests (unit + E2E):
```bash
make test
```

### End-to-end tests only:
```bash
make test-e2e
```

### With test runner script:
```bash
python scripts/run_e2e_tests.py
```

### Specific test class:
```bash
python scripts/run_e2e_tests.py TestConvertBasic
```

## Test Coverage

### 7 Test Classes, 15+ Test Methods:

1. **TestFloorCommand** - Floor detection
2. **TestConvertDryRun** - Debug mesh export
3. **TestConvertBasic** - Basic conversion
4. **TestConvertWithVerify** - Geometry verification
5. **TestConvertOptions** - CLI options
6. **TestErrorHandling** - Edge cases
7. **TestMiniIntegration** - Generated fixtures

## Installation

### Basic (no verify):
```bash
pip install -e ".[test]"
```

### With verify support:
```bash
pip install -e ".[test,verify]"
# or
make install-verify
```

## What Gets Tested

✅ Floor detection and debug export  
✅ Dry-run mode (body/slab/pre-union export)  
✅ STL output generation  
✅ Custom output paths  
✅ Module detection override  
✅ Geometry verification (with rtree/scipy)  
✅ Replace height options  
✅ Floor epsilon configuration  
✅ Error handling (missing files, missing ref tile)  
✅ Programmatic fixture support  

## Features

- **Auto-cleanup** - Cleans debug/ and out/ before/after each test
- **Smart skipping** - Skips tests when fixtures or dependencies missing
- **Detailed assertions** - Clear error messages with stdout/stderr
- **Multiple fixtures** - Real samples + generated geometry
- **CI-ready** - Works in GitHub Actions

## Documentation

See `tests/TEST_HARNESS.md` for complete documentation.
