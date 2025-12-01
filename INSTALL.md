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

- **Python**: 3.9 or higher
- **pip**: Latest version recommended
- **Dependencies**: 
  - `pyedflib >= 0.1.30`
  - `numpy >= 1.20.0`
  - `pandas >= 1.3.0`
  - `pydantic >= 2.0.0`
  - `python-dateutil >= 2.8.0`

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

For development, install in editable mode with all dependencies:

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

### Optional Dependencies

If you need development tools:

```bash
pip install cpap-py[dev]
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
from cpap_py import CPAPReader

# Test basic functionality
print("✓ cpap-py imported successfully!")
print(f"Version: {cpap_py.__version__}")

# You can now use the library with actual CPAP data
# reader = CPAPReader("/path/to/sdcard")
```

Run it:

```bash
python test_install.py
```

### Run Tests

If you installed from source:

```bash
# Run the test suite
./run_tests.sh unit

# Or use pytest directly
pytest tests/ -v
```

## Troubleshooting

### Common Issues

#### Import Error: No module named 'cpap_py'

**Solution**: Make sure you've installed the package:
```bash
pip install cpap-py
# or for development:
pip install -e ".[dev]"
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

#### Dependency Conflicts

**Solution**: Use a fresh virtual environment:
```bash
python -m venv fresh_env
source fresh_env/bin/activate
pip install cpap-py
```

#### pyedflib Installation Issues

If you encounter issues with pyedflib (requires compilation):

**On Linux**:
```bash
sudo apt-get install python3-dev
pip install cpap-py
```

**On macOS**:
```bash
# Ensure Xcode command line tools are installed
xcode-select --install
pip install cpap-py
```

**On Windows**:
- Ensure you have Microsoft Visual C++ Build Tools installed
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

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
