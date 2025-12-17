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

- Python 3.8+
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
├── tests/                    # Test suite (to be created)
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

Tests will be created as the project develops. For now, manual testing can be done with sample CPAP data.

### Running Tests (Future)

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_edf_parser.py

# Run with coverage
pytest --cov=cpap_py --cov-report=html
```

### Writing Tests

Tests should be placed in the `tests/` directory with filenames matching `test_*.py`.

```python
# tests/test_example.py
import pytest
from cpap_py import EDFParser

def test_edf_parser_init():
    parser = EDFParser("test.edf")
    assert parser.filepath.name == "test.edf"

def test_parse_header():
    parser = EDFParser("tests/data/test.edf")
    assert parser.parse_header() == True
    assert parser.header.num_signals > 0
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
