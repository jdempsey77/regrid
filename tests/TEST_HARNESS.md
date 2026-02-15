# Test Harness

Comprehensive end-to-end test suite for regrid.

## Quick Start

```bash
# Install with test dependencies
pip install -e ".[test,verify]"

# Run all end-to-end tests
make test-e2e

# Or use the test harness script
python scripts/run_e2e_tests.py

# Run specific test class
python scripts/run_e2e_tests.py TestConvertBasic

# Run all tests (including unit tests)
make test
```

## Test Structure

### `test_e2e.py` - End-to-End Integration Tests

Comprehensive integration tests that exercise the full regrid pipeline:

#### Test Classes:

1. **`TestFloorCommand`** - Floor detection subcommand
   - `test_floor_detection_on_sample` - Detects floor and exports debug plane
   - `test_floor_verbose` - Verbose output shows area stability

2. **`TestConvertDryRun`** - Convert with --dry-run (no output file)
   - `test_dry_run_exports_debug_meshes` - Exports body/slab/pre_union
   - `test_dry_run_with_export_debug` - Alternative --export-debug flag

3. **`TestConvertBasic`** - Basic convert operations
   - `test_convert_creates_output` - Creates output STL
   - `test_convert_with_custom_output` - Custom --out path
   - `test_convert_with_modules_override` - Override module detection

4. **`TestConvertWithVerify`** - Convert with verification (requires rtree/scipy)
   - `test_convert_verify_passes` - Verify passes on sample
   - `test_convert_verify_with_strict_tolerance` - Strict tolerance handling

5. **`TestConvertOptions`** - Various command options
   - `test_no_preserve_floor` - Fixed replace height mode
   - `test_custom_replace_height` - Custom replace height
   - `test_custom_floor_epsilon` - Custom floor epsilon

6. **`TestErrorHandling`** - Error handling and edge cases
   - `test_nonexistent_input_file` - Graceful failure on missing input
   - `test_missing_ref_tile` - Graceful failure on missing ref tile

7. **`TestMiniIntegration`** - Tests with programmatic fixtures
   - `test_mini_bin_end_to_end` - Full pipeline with generated geometry

## Test Fixtures

- **`sample_42_stl`** - Real 42mm sample file from `samples/`
- **`ref_tile`** - Reference 21mm tile from `refs/`
- **`mini_bin_stl`** - Programmatically generated test geometry
- **`cleanup_output_dirs`** - Auto-cleanup of `debug/` and `out/` before/after tests

## Running Tests

### Run all tests:
```bash
make test
```

### Run only end-to-end tests:
```bash
make test-e2e
```

### Run specific test class:
```bash
pytest tests/test_e2e.py::TestFloorCommand -v
```

### Run specific test:
```bash
pytest tests/test_e2e.py::TestConvertBasic::test_convert_creates_output -v
```

### Run with live output (see regrid CLI output):
```bash
pytest tests/test_e2e.py -v -s
```

## Test Dependencies

### Core (required):
- pytest
- trimesh
- numpy
- manifold3d

### Optional (for verify tests):
- rtree
- scipy

Install all with:
```bash
pip install -e ".[test,verify]"
```

## Continuous Integration

The GitHub Actions workflow (`.github/workflows/tests.yml`) runs:
- All unit tests
- All end-to-end tests
- Tests with verify enabled

Tests automatically skip if:
- Sample files are missing
- Reference tile is missing
- Optional dependencies (rtree/scipy) are not installed

## Adding New Tests

1. Add test method to appropriate class in `test_e2e.py`
2. Use fixtures for sample files and cleanup
3. Use `run_regrid()` helper to invoke CLI
4. Check return code and output
5. Verify output files exist and are non-empty

Example:
```python
def test_my_feature(self, sample_42_stl: Path, ref_tile: Path):
    """Test description."""
    result = run_regrid("convert", str(sample_42_stl), "--my-option")
    
    assert result.returncode == 0, (
        f"Command failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    
    output = result.stdout + result.stderr
    assert "Expected string" in output
    
    # Check output file
    output_file = OUT_DIR / "expected_output.stl"
    assert output_file.exists()
    assert output_file.stat().st_size > 0
```

## Debugging Failed Tests

### View full output:
```bash
pytest tests/test_e2e.py::TestName::test_name -v -s
```

### Keep debug files (comment out cleanup):
Edit `test_e2e.py` and comment out the cleanup fixture's `shutil.rmtree()` calls.

### Run regrid CLI manually:
```bash
python -m regrid convert samples/sample_42_1x1.stl --export-debug
ls -lh debug/
ls -lh out/
```

## CI/CD Integration

Tests run on every push and PR via GitHub Actions. The workflow:
1. Sets up Python 3.11
2. Installs dependencies with verify extras
3. Runs full test suite
4. Reports results

View results: https://github.com/jdempsey77/regrid/actions
