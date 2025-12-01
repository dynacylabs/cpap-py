# Test Suite for cpap-py

This directory contains a comprehensive test suite for the cpap-py library, designed to achieve >95% code coverage.

## Test Structure

The test suite is organized to mirror the source code structure and follows the template from `submodules/py-template`:

### Test Files

- **`test_init.py`** - Tests for package initialization and exports
- **`test_models.py`** - Tests for Pydantic data models (Device, Session, Event, etc.)
- **`test_reader.py`** - Tests for the main CPAPReader API
- **`test_settings.py`** - Tests for settings proposals and validation
- **`test_crc_parser.py`** - Tests for CRC validation
- **`test_edf_parser.py`** - Tests for EDF file parsing
- **`test_str_parser.py`** - Tests for STR.edf summary file parsing
- **`test_tgt_parser.py`** - Tests for TGT settings file parsing
- **`test_utils.py`** - Tests for utility functions and constants
- **`test_edge_cases.py`** - Tests for error handling and edge cases
- **`test_integration.py`** - Integration tests with real CPAP data

### Test Configuration

- **`conftest.py`** - Pytest fixtures and test configuration
- **`pytest.ini`** - Pytest and coverage settings (configured for 95% coverage requirement)

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=cpap_py --cov-report=term-missing --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests only (slower, requires sample data)
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Run Specific Test Files

```bash
pytest tests/test_models.py
pytest tests/test_reader.py -v
```

### Run Specific Test Classes or Methods

```bash
pytest tests/test_models.py::TestDevice
pytest tests/test_reader.py::TestCPAPReaderInit::test_reader_init_valid_path
```

## Test Markers

Tests are marked with the following categories:

- **`@pytest.mark.unit`** - Unit tests with mocked dependencies (fast)
- **`@pytest.mark.integration`** - Integration tests that use real data files
- **`@pytest.mark.slow`** - Tests that take significant time to run

## Fixtures

Common fixtures are defined in `conftest.py`:

### Data Fixtures

- `sample_data_dir` - Path to sample CPAP data directory
- `sample_datalog_dir` - Path to sample DATALOG directory
- `sample_settings_dir` - Path to sample SETTINGS directory
- `sample_brp_file` - Path to sample BRP (pressure) file
- `sample_eve_file` - Path to sample EVE (events) file
- `test_output_dir` - Temporary directory for test output

### Mock Fixtures

- `mock_device_settings` - Mock device settings dictionary
- `mock_session_summary` - Mock session summary dictionary
- `mock_waveform_data` - Mock waveform data array
- `mock_events` - Mock event list

## Coverage Requirements

The test suite is designed to achieve **>95% code coverage** as specified in `pytest.ini`:

```ini
--cov-fail-under=95
```

### Coverage Reports

After running tests, coverage reports are available:

- **Terminal**: Shows missing lines directly in console
- **HTML**: Open `htmlcov/index.html` in a browser for detailed coverage visualization

### Checking Coverage

```bash
# Generate coverage report
pytest --cov=cpap_py --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=cpap_py --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Organization

### Unit Tests

Unit tests focus on individual components with mocked dependencies:

- Fast execution
- Isolated component testing
- No file I/O when possible
- Extensive use of mocks and fixtures

### Integration Tests

Integration tests verify components work together:

- Use real CPAP data files from `data/` directory
- Test complete workflows
- Verify file parsing accuracy
- May skip if sample data not available

### Edge Case Tests

Edge case tests verify error handling:

- Invalid inputs
- Boundary conditions
- Error states
- Unusual data patterns

## Writing New Tests

When adding new functionality, follow these guidelines:

1. **Create tests first** (TDD approach)
2. **Use appropriate markers** (`@pytest.mark.unit`, etc.)
3. **Add docstrings** to test methods
4. **Use fixtures** for common test data
5. **Test edge cases** and error conditions
6. **Maintain >95% coverage**

### Example Test Structure

```python
import pytest
from cpap_py.module import MyClass

@pytest.mark.unit
class TestMyClass:
    """Test MyClass functionality."""
    
    def test_basic_functionality(self):
        """Test basic usage of MyClass."""
        obj = MyClass(param="value")
        assert obj.method() == expected_result
    
    def test_error_handling(self):
        """Test that errors are raised appropriately."""
        with pytest.raises(ValueError):
            MyClass(param="invalid")
    
    def test_edge_case(self):
        """Test edge case behavior."""
        obj = MyClass(param=None)
        assert obj.method() is None
```

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:

- All tests should pass
- Coverage must be ≥95%
- No warnings or errors
- Tests should be deterministic

## Dependencies

Test dependencies are specified in `pyproject.toml`:

```toml
[project.optional-dependencies]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "coverage>=7.0.0",
]
```

Install test dependencies:

```bash
pip install -e ".[test]"
```

## Troubleshooting

### Tests Fail Due to Missing Sample Data

Some integration tests require sample CPAP data files in the `data/` directory. These tests will skip if data is not available:

```python
if not Path(sample_data_dir).exists():
    pytest.skip("Sample data not available")
```

### Coverage Below 95%

If coverage is below the required threshold:

1. Run with `--cov-report=term-missing` to see uncovered lines
2. Add tests for missing coverage
3. Review edge cases and error paths
4. Check for untested private methods

### Import Errors

Ensure the package is installed in development mode:

```bash
pip install -e .
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
