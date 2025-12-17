# Installation Guide

This guide covers installation of cpap-py for different use cases.

## Table of Contents

- [Requirements](#requirements)
- [Quick Install](#quick-install)
- [Installation Methods](#installation-methods)
- [Development Installation](#development-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Upgrading](#upgrading)
- [Uninstalling](#uninstalling)

## Requirements

### System Requirements

- **Python**: 3.9, 3.10, 3.11, or 3.12
- **pip**: Latest version recommended (comes with Python)
- **Operating System**: Linux, macOS, or Windows

### Dependencies

**None!** cpap-py is a pure Python library using only the standard library. No external dependencies are required for basic usage.

### Optional Development Dependencies

For development and testing:
- pytest >= 7.0.0
- pytest-cov >= 4.0.0
- pytest-mock >= 3.10.0
- coverage >= 7.0.0
- black >= 23.0.0
- ruff >= 0.1.0

## Quick Install

For most users, installation is simple:

```bash
pip install cpap-py
```

That's it! You can now use cpap-py in your Python projects.

## Installation Methods

### Method 1: Install from PyPI (Recommended)

Install the latest stable release from the Python Package Index:

```bash
pip install cpap-py
```

To install a specific version:

```bash
pip install cpap-py==0.1.0
```

To install with development tools:

```bash
pip install cpap-py[dev]
```

### Method 2: Install from GitHub

Install the latest development version directly from GitHub:

```bash
pip install git+https://github.com/dynacylabs/cpap-py.git
```

Install a specific branch or tag:

```bash
# Install from specific branch
pip install git+https://github.com/dynacylabs/cpap-py.git@develop

# Install from specific tag
pip install git+https://github.com/dynacylabs/cpap-py.git@v0.1.0
```

### Method 3: Install from Source

Clone the repository and install locally:

```bash
# Clone repository
git clone https://github.com/dynacylabs/cpap-py.git
cd cpap-py

# Install
pip install .
```

### Method 4: Install in Virtual Environment (Recommended)

Using a virtual environment is recommended to avoid package conflicts:

**Using venv (built-in):**

```bash
# Create virtual environment
python -m venv cpap-env

# Activate virtual environment
# On Linux/macOS:
source cpap-env/bin/activate
# On Windows:
cpap-env\Scripts\activate

# Install cpap-py
pip install cpap-py
```

**Using conda:**

```bash
# Create conda environment
conda create -n cpap-py python=3.11

# Activate environment
conda activate cpap-py

# Install cpap-py
pip install cpap-py
```

## Development Installation

For contributors and developers:

### 1. Clone Repository

```bash
git clone https://github.com/dynacylabs/cpap-py.git
cd cpap-py
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install in Editable Mode

Install with development dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- The cpap-py package in editable mode
- All development dependencies (pytest, black, ruff, etc.)

### 4. Verify Development Setup

```bash
# Run tests
./run_tests.sh

# Check installation
python -c "from cpap_py import CPAPLoader; print('Success!')"

# Run linter
ruff check src/

# Format code
black src/ tests/
```

## Verification

After installation, verify cpap-py is working correctly:

### Quick Verification

```bash
# Check version
python -c "import cpap_py; print(cpap_py.__version__)"

# Test basic import
python -c "from cpap_py import CPAPLoader; print('Success!')"
```

### Comprehensive Verification

Create a file `test_install.py`:

```python
#!/usr/bin/env python
"""Test cpap-py installation"""

import cpap_py

print("Testing cpap-py installation...")
print(f"✓ cpap-py version: {cpap_py.__version__}")

# Test all imports
try:
    from cpap_py import (
        CPAPLoader,
        IdentificationParser,
        STRParser,
        DatalogParser,
        SettingsParser,
        EDFParser,
        MachineInfo,
        STRRecord,
        SessionData,
        EDFHeader,
        EDFSignal,
    )
    print("✓ All modules imported successfully!")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)

# Test basic functionality
try:
    loader = CPAPLoader(".")
    print("✓ CPAPLoader instantiated successfully!")
except Exception as e:
    print(f"✗ Error creating CPAPLoader: {e}")
    exit(1)

print("\n✓ Installation verified successfully!")
```

Run the test:

```bash
python test_install.py
```

Expected output:
```
Testing cpap-py installation...
✓ cpap-py version: 0.1.0
✓ All modules imported successfully!
✓ CPAPLoader instantiated successfully!

✓ Installation verified successfully!
```

## Troubleshooting

### Common Issues

#### Issue: `pip: command not found`

**Solution:** Install or upgrade pip:

```bash
# Download get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# Install pip
python get-pip.py

# Or upgrade pip
python -m pip install --upgrade pip
```

#### Issue: `ModuleNotFoundError: No module named 'cpap_py'`

**Possible causes and solutions:**

1. **Wrong Python environment:**
   ```bash
   # Check which Python you're using
   which python
   python --version
   
   # Ensure pip installs to the correct Python
   python -m pip install cpap-py
   ```

2. **Not installed:**
   ```bash
   pip install cpap-py
   ```

3. **Virtual environment not activated:**
   ```bash
   source venv/bin/activate  # Or your venv activation command
   ```

#### Issue: `Permission denied` during installation

**Solution:** Use `--user` flag or virtual environment:

```bash
# Install for current user only
pip install --user cpap-py

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install cpap-py
```

#### Issue: `ImportError` after installation

**Solution:** Reinstall in clean environment:

```bash
# Create fresh virtual environment
python -m venv fresh-env
source fresh-env/bin/activate
pip install --upgrade pip
pip install cpap-py
```

#### Issue: Old version installed

**Solution:** Force upgrade:

```bash
pip install --upgrade --force-reinstall cpap-py
```

#### Issue: Development dependencies not installing

**Solution:** Ensure you're using quotes around `[dev]`:

```bash
# Correct:
pip install "cpap-py[dev]"
pip install -e ".[dev]"

# May fail in some shells:
pip install cpap-py[dev]  # Missing quotes
```

### Platform-Specific Issues

#### Windows

**Issue:** `'python' is not recognized`

**Solution:**
1. Ensure Python is in your PATH
2. Try using `py` instead of `python`:
   ```cmd
   py -m pip install cpap-py
   ```

**Issue:** Permission errors on Windows

**Solution:** Run terminal as Administrator, or use `--user` flag.

#### macOS

**Issue:** Multiple Python versions installed

**Solution:** Use `python3` explicitly:
```bash
python3 -m pip install cpap-py
```

#### Linux

**Issue:** System Python protected

**Solution:** Use virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install cpap-py
```

### Getting Help

If you continue to have issues:

1. **Check Python version:** `python --version` (must be 3.9+)
2. **Check pip version:** `pip --version`
3. **Update pip:** `python -m pip install --upgrade pip`
4. **Create minimal reproduction:**
   ```bash
   python -m venv test-env
   source test-env/bin/activate
   pip install cpap-py
   python -c "import cpap_py; print('OK')"
   ```
5. **Open an issue:** [GitHub Issues](https://github.com/dynacylabs/cpap-py/issues)

## Upgrading

### Upgrade to Latest Version

```bash
pip install --upgrade cpap-py
```

### Upgrade to Specific Version

```bash
pip install --upgrade cpap-py==0.2.0
```

### Check Current Version

```bash
pip show cpap-py
# or
python -c "import cpap_py; print(cpap_py.__version__)"
```

## Uninstalling

### Remove cpap-py

```bash
pip uninstall cpap-py
```

### Remove cpap-py and Development Dependencies

```bash
# Uninstall cpap-py
pip uninstall cpap-py

# If you installed dev dependencies separately
pip uninstall pytest pytest-cov pytest-mock coverage black ruff
```

### Complete Cleanup

If you used a virtual environment:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment directory
rm -rf venv  # or your venv name
```

## Next Steps

After successful installation:

1. **Read the documentation:**
   - [README.md](README.md) - Quick start and API reference
   - [USAGE.md](USAGE.md) - Detailed usage examples
   - [DEVELOPMENT.md](DEVELOPMENT.md) - Development guide

2. **Try the examples:**
   ```python
   from cpap_py import CPAPLoader
   
   loader = CPAPLoader("path/to/cpap/data")
   data = loader.load_all()
   print(f"Device: {data.machine_info.model}")
   ```

3. **Run the tests:**
   ```bash
   # Clone repository
   git clone https://github.com/dynacylabs/cpap-py.git
   cd cpap-py
   
   # Run tests
   ./run_tests.sh
   ```

4. **Contribute:**
   - See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
   - Open issues or pull requests on GitHub

## Additional Resources

- **GitHub Repository:** [https://github.com/dynacylabs/cpap-py](https://github.com/dynacylabs/cpap-py)
- **Issue Tracker:** [https://github.com/dynacylabs/cpap-py/issues](https://github.com/dynacylabs/cpap-py/issues)
- **PyPI Package:** [https://pypi.org/project/cpap-py/](https://pypi.org/project/cpap-py/)
- **Documentation:** [GitHub README](https://github.com/dynacylabs/cpap-py/blob/main/README.md)


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
