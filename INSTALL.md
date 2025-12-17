# Installation Guide

This guide covers how to install cpap-py.

## Table of Contents

- [Requirements](#requirements)
- [Installation Methods](#installation-methods)
  - [From PyPI (Recommended)](#from-pypi-recommended)
  - [From Source](#from-source)
  - [Development Installation](#development-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Requirements

- **Python**: 3.8 or higher
- **pip**: Latest version recommended
- **Dependencies**: None! cpap-py uses only the Python standard library

## Installation Methods

### From PyPI (Recommended)

The easiest way to install the library is from PyPI using pip:

```bash
pip install cpap-py
```

To upgrade to the latest version:

```bash
pip install --upgrade cpap-py
```

To install a specific version:

```bash
pip install cpap-py==0.1.0
```

### From Source

To install directly from the GitHub repository:

```bash
# Clone the repository
git clone https://github.com/dynacylabs/cpap-py.git
cd cpap-py

# Install
pip install .
```

Or install directly from GitHub without cloning:

```bash
pip install git+https://github.com/dynacylabs/cpap-py.git
```

### Development Installation

For development, install in editable mode with test dependencies:

```bash
# Clone the repository
git clone https://github.com/dynacylabs/cpap-py.git
cd cpap-py

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

This allows you to make changes to the code and see them reflected immediately without reinstalling.

### Development Dependencies

If you need development and testing tools:

```bash
pip install -e ".[dev]"
```

This includes:
- pytest and plugins for testing
- black for code formatting
- ruff for linting
- mypy for type checking
- coverage tools

## Verification

After installation, verify it's working correctly:

### Command Line Verification

```bash
python -c "import cpap_py; print(cpap_py.__version__)"
```

### Python Script Verification

Create a file `test_install.py`:

```python
import cpap_py

# Test basic functionality
print("✓ cpap-py imported successfully!")
print(f"Version: {cpap_py.__version__}")

# Verify all modules are accessible
from cpap_py import CPAPLoader, IdentificationParser, STRParser
from cpap_py import DatalogParser, SettingsParser, EDFParser
print("✓ All modules imported successfully!")
```

Run it:

```bash
python test_install.py
```

### Run Tests

If you installed from source with dev dependencies:

```bash
# Run the test suite
pytest tests/ -v
```

## Troubleshooting

### Common Issues

#### Import Error: No module named 'cpap_py'

**Solution**: Make sure you've installed the package:
```bash
pip install cpap-py
# or for development:
pip install -e .
```

#### Permission Denied Error

**Solution**: Use `--user` flag or a virtual environment:
```bash
pip install --user cpap-py
```

Or create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install cpap-py
```

#### Old Version Installed

**Solution**: Force reinstall:
```bash
pip install --upgrade --force-reinstall cpap-py
```

#### Python Version Too Old

cpap-py requires Python 3.8 or higher. Check your version:
```bash
python --version
```

If you have an older version, upgrade Python or use a newer environment.

### Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/dynacylabs/cpap-py/issues) for similar problems
2. Search the [Discussions](https://github.com/dynacylabs/cpap-py/discussions)
3. Create a new issue with:
   - Your Python version (`python --version`)
   - Your pip version (`pip --version`)
   - Your operating system
   - The full error message
   - Steps to reproduce the issue

## Next Steps

- Read the [Usage Guide](USAGE.md) to learn how to use the library
- Check the [Development Guide](DEVELOPMENT.md) for contributing
- Review the main [README](README.md) for API reference
