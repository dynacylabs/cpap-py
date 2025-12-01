# Development Guide

This guide covers the development workflow, testing, and release process for cpap-py.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Code Coverage](#code-coverage)
- [Development Workflow](#development-workflow)
- [Release Process](#release-process)
- [Continuous Integration](#continuous-integration)
- [Debugging](#debugging)
- [Performance](#performance)

## Development Setup

### Prerequisites

- Python 3.9+
- Git
- pip
- Virtual environment tool (venv, virtualenv, or conda)

### Initial Setup

1. **Clone the Repository**

```bash
git clone https://github.com/dynacylabs/cpap-py.git
cd cpap-py
```

2. **Create Virtual Environment**

```bash
# Using venv (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Using conda
conda create -n cpap-py python=3.11
conda activate cpap-py
```

3. **Install Development Dependencies**

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"
```

4. **Verify Installation**

```bash
# Run tests
./run_tests.sh unit

# Check imports
python -c "from cpap_py import CPAPReader; print('Success!')"
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Python Test Explorer
- Coverage Gutters
- GitLens

Recommended settings (`.vscode/settings.json`):

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.analysis.typeCheckingMode": "basic",
    "editor.formatOnSave": true,
    "editor.rulers": [100],
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

#### PyCharm

1. Mark `src/` as Sources Root
2. Enable pytest as test runner
3. Configure Python 3.9+ interpreter
4. Enable type checking
5. Set Black as code formatter

## Project Structure

```
cpap-py/
├── src/cpap_py/            # Main package
│   ├── __init__.py         # Package exports
│   ├── reader.py           # CPAPReader main API
│   ├── models.py           # Pydantic data models
│   ├── settings.py         # Settings models and proposals
│   ├── parsers/            # File parsers
│   │   ├── __init__.py
│   │   ├── edf_parser.py   # Standard EDF parser
│   │   ├── str_parser.py   # Custom STR.edf parser
│   │   ├── tgt_parser.py   # Settings file parser
│   │   └── crc_parser.py   # CRC verification
│   └── utils/              # Utilities
│       ├── __init__.py
│       └── constants.py    # Channel IDs, event types
├── tests/                  # Test suite (13 files)
│   ├── __init__.py
│   ├── conftest.py         # Shared fixtures
│   ├── README.md           # Test documentation
│   ├── test_init.py        # Package initialization tests
│   ├── test_models.py      # Model tests
│   ├── test_reader.py      # Reader tests
│   ├── test_settings.py    # Settings tests
│   ├── test_crc_parser.py  # CRC parser tests
│   ├── test_edf_parser.py  # EDF parser tests
│   ├── test_str_parser.py  # STR parser tests
│   ├── test_tgt_parser.py  # TGT parser tests
│   ├── test_utils.py       # Utilities tests
│   ├── test_edge_cases.py  # Edge case tests
│   └── test_integration.py # Integration tests
├── data/                   # Sample CPAP data (anonymized)
│   ├── Identification.crc
│   ├── Identification.tgt
│   ├── STR.edf
│   ├── DATALOG/
│   └── SETTINGS/
├── docs/                   # Additional documentation
├── .github/                # GitHub configuration
│   └── workflows/          # CI/CD workflows
├── .gitignore
├── LICENSE
├── MANIFEST.in             # Package manifest
├── README.md               # Project overview
├── INSTALL.md              # Installation guide
├── USAGE.md                # Usage examples and API
├── CONTRIBUTING.md         # Contribution guidelines
├── DEVELOPMENT.md          # This file
├── pyproject.toml          # Project configuration
├── pytest.ini              # Pytest configuration
├── requirements.txt        # Runtime dependencies
├── requirements-test.txt   # Test dependencies
└── run_tests.sh            # Test runner script
```

### Directory Organization

**Source Code (`src/cpap_py/`):**
- Main package containing all production code
- Parsers in `parsers/` subdirectory
- Utilities in `utils/` subdirectory
- Clear separation of concerns

**Tests (`tests/`):**
- One test file per module
- Shared fixtures in `conftest.py`
- Integration tests separate from unit tests
- Test documentation in `tests/README.md`

**Documentation:**
- README.md - Project overview and quick start
- INSTALL.md - Installation instructions
- USAGE.md - API documentation and examples
- CONTRIBUTING.md - Contribution guidelines
- DEVELOPMENT.md - Development workflow (this file)

**Configuration:**
- `pyproject.toml` - Project metadata and dependencies
- `pytest.ini` - Test configuration
- `.github/workflows/` - CI/CD pipelines

## Testing

### Running Tests

Use the provided test runner script:

```bash
# Run all tests
./run_tests.sh

# Run only unit tests (fast)
./run_tests.sh unit

# Run integration tests
./run_tests.sh integration

# Run with coverage report
./run_tests.sh coverage

# Run specific test file
./run_tests.sh tests/test_edf_parser.py

# Run specific test
./run_tests.sh tests/test_reader.py::TestCPAPReader::test_load_devices
```

Or use pytest directly:

```bash
# All tests
pytest

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "test_edf"

# Run tests with marker
pytest -m unit
pytest -m integration
pytest -m slow
```

### Writing Tests

Follow these guidelines:

1. **Location**: Place tests in `tests/` directory
2. **Naming**: Name test files `test_*.py`
3. **Structure**: Group related tests in classes
4. **Markers**: Use pytest markers (`@pytest.mark.unit`, etc.)
5. **Fixtures**: Use fixtures from `conftest.py`
6. **Data**: Use sample data from `data/` directory

Example test structure:

```python
import pytest
from cpap_py import CPAPReader
from cpap_py.parsers.edf_parser import EDFParser

@pytest.mark.unit
class TestEDFParser:
    """Tests for the EDF parser."""
    
    def test_parse_valid_file(self, sample_edf_file):
        """Test parsing a valid EDF file."""
        parser = EDFParser(sample_edf_file)
        signals = parser.get_signals()
        assert len(signals) > 0
    
    def test_invalid_file_raises_error(self):
        """Test that invalid file raises appropriate error."""
        with pytest.raises(ValueError):
            parser = EDFParser("nonexistent.edf")
```

### Test Markers

Available markers (defined in `pytest.ini`):

- `@pytest.mark.unit`: Unit tests (fast, mocked)
- `@pytest.mark.integration`: Integration tests (use real files)
- `@pytest.mark.slow`: Slow-running tests

Usage:

```python
@pytest.mark.unit
def test_fast_operation():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_full_data_load():
    pass
```

Run specific markers:

```bash
pytest -m unit              # Only unit tests
pytest -m "not slow"        # Exclude slow tests
pytest -m "unit and not slow"  # Unit tests, excluding slow
```

## Code Coverage

### Measuring Coverage

```bash
# Generate coverage report
./run_tests.sh coverage

# View in terminal
coverage report

# Generate HTML report
coverage html
# Open htmlcov/index.html in browser

# Generate XML report (for CI)
coverage xml
```

### Coverage Goals

- **Overall**: 95%+ coverage
- **New Code**: 100% coverage
- **Critical Paths**: 100% coverage (parsers, CRC validation)

### Checking Coverage Locally

```bash
# Run tests with coverage
pytest --cov=cpap_py --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=cpap_py --cov-report=term --cov-fail-under=95
```

## Development Workflow

### Daily Development

1. **Pull Latest Changes**

```bash
git checkout main
git pull origin main
```

2. **Create Feature Branch**

```bash
git checkout -b feature/add-resvent-support
```

3. **Make Changes**

- Edit code
- Add tests
- Update docs

4. **Run Tests**

```bash
./run_tests.sh
```

5. **Format and Lint**

```bash
# Format with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type check with MyPy
mypy src/cpap_py/
```

6. **Commit Changes**

```bash
git add .
git commit -m "feat: Add support for Resvent iBreeze files"
```

7. **Push and Create PR**

```bash
git push origin feature/add-resvent-support
# Then create PR on GitHub
```

### Code Quality Tools

#### Black (Code Formatting)

```bash
# Format all code
black src/ tests/

# Check formatting without changing
black --check src/ tests/

# Format specific file
black src/cpap_py/reader.py
```

Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 100
target-version = ['py39']
```

#### Ruff (Linting)

```bash
# Lint all code
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Lint specific file
ruff check src/cpap_py/reader.py
```

#### MyPy (Type Checking)

```bash
# Type check package
mypy src/cpap_py/

# Strict mode
mypy --strict src/cpap_py/

# Check specific file
mypy src/cpap_py/reader.py
```

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Creating a Release

1. **Update Version**

Update version in `pyproject.toml`:

```toml
[project]
name = "cpap-py"
version = "0.2.0"
```

2. **Update Changelog**

Add release notes to README.md changelog section.

3. **Commit Changes**

```bash
git add pyproject.toml README.md
git commit -m "chore: Bump version to 0.2.0"
git push origin main
```

4. **Create and Push Tag**

```bash
# Create annotated tag
git tag -a v0.2.0 -m "Release version 0.2.0"

# Push tag
git push origin v0.2.0
```

5. **Create GitHub Release**

- Go to GitHub Releases
- Click "Draft a new release"
- Select the tag
- Fill in release notes
- Publish release

6. **Publish to PyPI**

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Upload to TestPyPI (for testing)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Continuous Integration

### GitHub Actions Workflows

The project includes four automated workflows in `.github/workflows/`:

#### 1. Tests Workflow (`tests.yml`)

**Triggers:**
- Push to main
- Pull requests
- Daily at 2am UTC (scheduled)
- Manual dispatch

**Actions:**
- Test on Python 3.9, 3.10, 3.11, 3.12 (matrix strategy)
- Run linting (Ruff) and type checking (MyPy)
- Code formatting check (Black)
- Generate coverage reports (95% threshold)
- Upload coverage to Codecov
- Upload HTML coverage report as artifact

#### 2. Security Workflow (`security.yml`)

**Triggers:**
- Push to main
- Pull requests
- Weekly on Mondays at 3am UTC
- Manual dispatch

**Scans:**
- **Dependency vulnerabilities** (Safety)
- **Code security issues** (Bandit)
- **Secret detection** (TruffleHog)
- **CodeQL analysis** (security-extended queries)

#### 3. Dependency Updates (`dependency-updates.yml`)

**Triggers:**
- Weekly on Mondays at 9am UTC
- Manual dispatch

**Actions:**
- Check for outdated packages
- Audit dependencies for vulnerabilities (pip-audit)
- Auto-create GitHub issues if vulnerabilities found

#### 4. Publish to PyPI (`publish-to-pypi.yml`)

**Triggers:**
- GitHub release published
- Manual dispatch

**Actions:**
- Build distribution packages
- Publish to PyPI using trusted publishing

### Local CI Simulation

Run the same checks locally:

```bash
# Run all tests like CI
pytest -v --cov=cpap_py --cov-report=term-missing

# Run linting
black --check src/ tests/
ruff check src/ tests/
mypy src/cpap_py/

# Security scan (if tools installed)
pip install safety bandit
safety check
bandit -r src/cpap_py/
```

## Debugging

### Using pdb

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Python 3.7+ breakpoint()
breakpoint()
```

### Using pytest debugger

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb
```

### Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
```

### Debugging EDF Files

```python
# Inspect EDF file structure
import pyedflib

f = pyedflib.EdfReader("data/DATALOG/20241126/20241127_004009_BRP.edf")
print(f"Signals: {f.signals_in_file}")
print(f"Duration: {f.file_duration}")

for i in range(f.signals_in_file):
    print(f"Signal {i}: {f.getLabel(i)}")
    print(f"  Samples: {f.getNSamples()[i]}")
    print(f"  Physical dimension: {f.getPhysicalDimension(i)}")

f.close()
```

## Performance

### Profiling

```python
# Using cProfile
python -m cProfile -o profile.stats script.py

# Analyze profile
python -m pstats profile.stats
# Then: sort time, stats 10
```

### Memory Profiling

```bash
# Install memory_profiler
pip install memory_profiler

# Profile script
python -m memory_profiler script.py
```

### Benchmarking

```python
import timeit

# Time a function
time = timeit.timeit(
    'reader.get_sessions()',
    setup='from cpap_py import CPAPReader; reader = CPAPReader("data")',
    number=100
)
print(f"Time: {time}")
```

### Optimization Tips

1. **Lazy Loading**: Only load waveforms when needed
2. **Filtering**: Use session filters to reduce memory
3. **CRC Validation**: Disable for performance-critical paths
4. **Batch Processing**: Process multiple files efficiently
5. **Caching**: Cache parsed results when appropriate

## Troubleshooting

### Common Issues

**Import errors after changes**:
```bash
pip install -e ".[dev]"
```

**Tests not found**:
```bash
# Ensure tests directory has __init__.py
# Check pytest.ini configuration
pytest --collect-only
```

**Coverage not working**:
```bash
# Reinstall in editable mode
pip uninstall cpap-py
pip install -e ".[dev]"
```

**pyedflib compilation issues**:
```bash
# Linux
sudo apt-get install python3-dev

# macOS
xcode-select --install
```

## Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [OSCAR Project](https://www.sleepfiles.com/OSCAR/)
- [EDF+ Specification](https://www.edfplus.info/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Getting Help

- Check GitHub Issues
- Read documentation
- Ask in GitHub Discussions
- Contact maintainers
