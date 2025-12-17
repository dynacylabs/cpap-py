# Development Guide

This guide covers the development workflow, testing, and contributing to cpap-py.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Code Style](#code-style)
- [Development Workflow](#development-workflow)
- [Contributing](#contributing)

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
./run_tests.sh

# Check imports
python -c "from cpap_py import CPAPLoader; print('Success!')"
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Python Test Explorer

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
3. Configure Python 3.8+ interpreter
4. Enable type checking
5. Set Black as code formatter

## Project Structure

```
cpap-py/
├── src/
│   └── cpap_py/              # Main package
│       ├── __init__.py       # Package initialization and exports
│       ├── edf_parser.py     # EDF file parser (pure Python)
│       ├── identification.py # Device identification parser
│       ├── str_parser.py     # STR.edf summary data parser
│       ├── datalog_parser.py # DATALOG session data parser
│       ├── settings_parser.py# Settings file parser
│       ├── loader.py         # High-level unified loader
│       └── utils.py          # Utility functions
├── tests/                    # Comprehensive test suite (97% coverage, 188 tests)
│   ├── conftest.py           # Pytest fixtures
│   ├── test_init.py          # Package initialization tests
│   ├── test_identification.py # ID parser tests
│   ├── test_edf_parser.py    # EDF parser tests
│   ├── test_utils.py         # Utility tests
│   ├── test_parser_core.py   # Core parser tests
│   ├── test_integration.py   # Integration tests
│   └── ...                   # Additional test files
├── setup.py                  # Package setup configuration
├── pyproject.toml            # Modern Python project configuration
├── requirements.txt          # Runtime dependencies (none!)
├── requirements-test.txt     # Test dependencies
├── README.md                 # Main documentation
├── INSTALL.md                # Installation guide
├── USAGE.md                  # Usage examples
├── DEVELOPMENT.md            # This file
├── CONTRIBUTING.md           # Contribution guidelines
└── LICENSE                   # MIT license
```

### Module Overview

- **edf_parser.py**: Pure Python implementation of EDF/EDF+ file format parser. No external dependencies.
- **identification.py**: Parses both .tgt (text) and .json format device identification files.
- **str_parser.py**: Parses STR.edf files containing daily summary statistics.
- **datalog_parser.py**: Parses session waveform data from DATALOG directory.
- **settings_parser.py**: Parses device settings from .tgt files in SETTINGS directory.
- **loader.py**: High-level interface that coordinates all parsers for easy data loading.
- **utils.py**: Helper functions for date handling, calculations, and data processing.

## Testing

The library includes a comprehensive test suite with **97% code coverage** and **188 automated tests**.

### Running Tests

```bash
# Run all tests with coverage
./run_tests.sh

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_edf_parser.py -v

# Run with coverage report
pytest tests/ --cov=cpap_py --cov-report=term-missing

# Run specific test
pytest tests/test_identification.py::TestIdentificationParser::test_parse_tgt_file -v
```

### Test Organization

Test files are organized by module:

- `test_init.py` - Package initialization tests
- `test_identification.py` - Device ID parser tests  
- `test_edf_parser.py` - EDF format parser tests
- `test_utils.py` - Utility function tests
- `test_parser_core.py` - Core parser functionality
- `test_integration.py` - Integration tests
- `test_mock_scenarios.py` - Mock-based tests
- `test_realistic_edf_data.py` - Realistic data tests
- `test_signal_combinations.py` - Signal combination tests
- `test_bilevel_modes.py` - BiLevel therapy mode tests
- `test_settings_alternative_signals.py` - Alternative signal tests
- `test_optional_signals_errors.py` - Error handling tests

See [TEST_SUITE.md](TEST_SUITE.md) for detailed test documentation.

### Writing Tests

Tests use pytest and should include:

```python
import pytest
from cpap_py import EDFParser

def test_edf_parser_basic():
    """Test basic EDF parser functionality"""
    parser = EDFParser("test.edf")
    assert parser is not None

def test_parse_with_fixture(sample_edf_file):
    """Test using fixture from conftest.py"""
    parser = EDFParser(str(sample_edf_file))
    assert parser.parse() == True
```

## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [Ruff](https://docs.astral.sh/ruff/) for linting
- Add type hints where beneficial

### Formatting Code

```bash
# Format with Black
black src/

# Check with Ruff
ruff check src/

# Auto-fix with Ruff
ruff check --fix src/

# Type checking with mypy (if installed)
mypy src/cpap_py
```

### Docstring Style

Use Google-style docstrings:

```python
def parse_file(filepath: str, validate: bool = True) -> bool:
    """
    Parse an EDF file from the given path.
    
    Args:
        filepath: Path to the EDF file
        validate: Whether to validate data integrity
        
    Returns:
        True if parsing succeeded, False otherwise
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    pass
```

## Development Workflow

### Making Changes

1. **Create a Branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make Your Changes**

- Write code
- Add/update tests (when test framework is in place)
- Update documentation
- Format code with Black
- Check with Ruff

3. **Test Your Changes**

```bash
# Test imports
python -c "from cpap_py import CPAPLoader"

# Check formatting
black --check src/
ruff check src/
```

4. **Commit Changes**

```bash
git add .
git commit -m "Add feature: description"
```

5. **Push and Create PR**

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues and pull requests when relevant

Examples:
```
Add EDF+ annotation parsing support

Fix memory leak in session data loading

Update documentation for new API

Refactor settings parser for better performance
```

## Contributing

### Before Contributing

1. Check existing [issues](https://github.com/dynacylabs/cpap-py/issues) and [pull requests](https://github.com/dynacylabs/cpap-py/pulls)
2. Open an issue to discuss major changes
3. Fork the repository
4. Create a feature branch

### Contribution Checklist

- [ ] Code follows project style guidelines
- [ ] New functionality tested manually
- [ ] Documentation updated
- [ ] Code formatted with Black
- [ ] Linting passes (Ruff)
- [ ] Commit messages are clear and descriptive

### Types of Contributions

- **Bug Reports**: Open an issue with reproducible steps
- **Bug Fixes**: Submit a PR with description
- **New Features**: Discuss in an issue first, then submit PR
- **Documentation**: Improvements always welcome
- **Tests**: Help create test suite
- **Performance**: Optimization PRs with benchmarks

### Code Review Process

1. At least one maintainer review required
2. All conversations must be resolved
3. No merge conflicts
4. Documentation updated if needed

## Getting Help

- Open an [issue](https://github.com/dynacylabs/cpap-py/issues) for bugs or questions
- Check existing documentation
- Review closed issues and PRs for similar problems

## Architecture Notes

### Why Pure Python?

This library is intentionally built with zero external dependencies:
- **Portability**: Works anywhere Python runs
- **Easy Installation**: No compilation or build tools needed
- **Reliability**: Fewer dependencies = fewer breaking changes
- **Transparency**: All code is readable and auditable

### EDF Parser Implementation

The EDF parser is implemented from scratch following the EDF specification:
- Reads binary data directly using Python's `struct` module
- Handles both compressed (.edf.gz) and uncompressed files
- Supports both EDF and EDF+ formats
- No dependency on pyedflib or other C extensions

## Release Process

(To be defined as project matures)

1. Update version in `setup.py` and `src/cpap_py/__init__.py`
2. Update CHANGELOG.md (when created)
3. Create git tag
4. Build and publish to PyPI

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
