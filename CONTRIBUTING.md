# Contributing to cpap-py

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background or experience level.

### Expected Behavior

- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Be patient with questions and discussions
- Respect differing viewpoints and experiences

### Unacceptable Behavior

- Harassment or discrimination of any kind
- Trolling, insulting, or derogatory comments
- Publishing others' private information
- Any conduct inappropriate for a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.9 or higher installed
- Git installed and configured
- A GitHub account
- Familiarity with pytest for testing
- Basic understanding of CPAP devices and EDF file format (helpful but not required)

### Repository Organization

The repository follows a clean, organized structure:

**Core Documentation (5 files only):**
- `README.md` - Project overview and quick start
- `INSTALL.md` - Installation instructions
- `USAGE.md` - API documentation and examples
- `CONTRIBUTING.md` - This file
- `DEVELOPMENT.md` - Development workflow

**Source Code:**
- `src/cpap_py/` - Main package
  - `parsers/` - File format parsers
  - `utils/` - Utilities and constants

**Tests (13 organized files):**
- `tests/` - Test suite with clear module mapping
  - `test_*.py` - One file per module
  - `conftest.py` - Shared fixtures
  - `README.md` - Test documentation

**Scripts:**
- `run_tests.sh` - Unified test runner

See DEVELOPMENT.md for detailed project structure.

### First-Time Contributors

If this is your first contribution:

1. **Find an Issue**: Look for issues labeled `good first issue` or `help wanted`
2. **Ask Questions**: Don't hesitate to ask for clarification in the issue comments
3. **Small Changes**: Start with small, manageable changes
4. **Read the Docs**: Familiarize yourself with the [Usage Guide](USAGE.md) and [Development Guide](DEVELOPMENT.md)

## Development Setup

See the [Development Guide](DEVELOPMENT.md) for detailed setup instructions.

Quick setup:

```bash
# Clone the repository
git clone https://github.com/dynacylabs/cpap-py.git
cd cpap-py

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify setup
./run_tests.sh unit
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug Fixes**: Fix issues reported in the issue tracker
- **New Features**: Add support for new file types, parsers, or analysis features
- **Documentation**: Improve docs, add examples, fix typos
- **Tests**: Add test coverage, improve test quality
- **Performance**: Optimize code for better performance
- **Refactoring**: Improve code structure and readability
- **Parser Improvements**: Enhance EDF parsing, add new signal types

### Reporting Bugs

When reporting bugs, include:

- **Clear Title**: Descriptive summary of the issue
- **Description**: Detailed explanation of the problem
- **Steps to Reproduce**: Exact steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: Python version, OS, package version
- **Sample Data**: If possible, include a minimal EDF file that reproduces the issue (anonymized)

Example bug report:

```markdown
**Title**: CRC validation fails on valid STR.edf file

**Description**: When parsing a valid STR.edf file with CRC validation enabled, 
the parser incorrectly reports a CRC mismatch.

**Steps to Reproduce**:
1. Create reader: `reader = CPAPReader("/path/to/data", crc_validation=CRCValidationMode.STRICT)`
2. Load sessions: `sessions = reader.get_sessions()`
3. Error occurs during STR.edf parsing

**Expected**: File should pass CRC validation
**Actual**: Raises CRCValidationError

**Environment**: Python 3.11, Ubuntu 24.04, cpap-py 0.1.0

**Sample**: (attach anonymized EDF file if possible)
```

### Suggesting Features

When suggesting new features:

1. **Check Existing Issues**: Search for similar feature requests
2. **Describe the Feature**: Clearly explain what you want
3. **Use Cases**: Provide real-world use cases
4. **Alternatives**: Mention alternatives you've considered
5. **Implementation Ideas**: Optional but helpful

### Making Changes

1. **Fork the Repository**

```bash
# Fork via GitHub UI, then clone
git clone https://github.com/YOUR-USERNAME/cpap-py.git
cd cpap-py
```

2. **Create a Branch**

```bash
# Create a descriptive branch name
git checkout -b feature/add-resvent-support
# or
git checkout -b fix/crc-validation-error
```

3. **Make Your Changes**

- Write clean, readable code
- Follow the style guide
- Add or update tests
- Update documentation

4. **Test Your Changes**

```bash
# Run all tests
./run_tests.sh

# Run specific tests
pytest tests/test_edf_parser.py -v

# Check coverage
./run_tests.sh coverage
```

5. **Commit Your Changes**

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: Add support for Resvent iBreeze files"
```

Follow commit message conventions:
- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Fix bug" not "Fixes bug"
- Keep first line under 50 characters
- Reference issues: "Fix CRC validation (#123)"
- Prefix with type: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

6. **Push to Your Fork**

```bash
git push origin feature/add-resvent-support
```

7. **Open a Pull Request**

- Go to your fork on GitHub
- Click "Pull Request"
- Fill in the PR template
- Link related issues

## Code Quality Standards

### Code Style

We use several tools to maintain code quality:

```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type check with MyPy
mypy src/cpap_py/
```

### Code Review Checklist

Before submitting, ensure:

- [ ] Code follows Python conventions (PEP 8)
- [ ] All tests pass
- [ ] New code has tests (aim for 95%+ coverage)
- [ ] Documentation is updated
- [ ] No linting errors
- [ ] Type hints are used where appropriate
- [ ] Docstrings are added for public APIs (Google style)
- [ ] Changes are backward compatible (or migration guide provided)
- [ ] Sample data files are anonymized (no patient information)

## Testing Requirements

### Writing Tests

- All new features must include tests
- Bug fixes should include regression tests
- Tests should be clear and well-documented
- Use descriptive test names
- Mark tests appropriately (`@pytest.mark.unit`, `@pytest.mark.integration`)

Example test:

```python
import pytest
from cpap_py import CPAPReader

@pytest.mark.unit
class TestCPAPReader:
    """Test the CPAPReader class."""
    
    def test_load_valid_directory(self, sample_data_dir):
        """Test that reader loads valid SD card directory."""
        reader = CPAPReader(sample_data_dir)
        devices = reader.get_devices()
        assert len(devices) > 0
        assert devices[0].serial_number is not None
```

### Running Tests

```bash
# All tests
./run_tests.sh

# Unit tests only
./run_tests.sh unit

# Integration tests
./run_tests.sh integration

# With coverage
./run_tests.sh coverage

# Specific file
pytest tests/test_edf_parser.py -v
```

### Test Coverage

- Aim for 95%+ code coverage
- 100% coverage for new features
- Tests should be meaningful, not just for coverage

Check coverage:

```bash
./run_tests.sh coverage
# Then open htmlcov/index.html
```

### Test Data

- Use anonymized sample data in `data/` directory
- Never commit real patient data
- Remove all identifying information from test files
- Document test data sources and characteristics

## Pull Request Process

1. **Update Documentation**: Ensure all docs are updated
2. **Add Tests**: Include comprehensive tests
3. **Update Changelog**: Add entry to README.md changelog section
4. **Follow Template**: Fill out the PR template completely
5. **Request Review**: Tag maintainers for review
6. **Address Feedback**: Respond to review comments promptly
7. **Keep Updated**: Rebase on main if needed

### PR Title Format

- `feat: Add support for BiPAP S/T devices`
- `fix: Resolve CRC validation error in STR parser`
- `docs: Update installation instructions`
- `test: Add tests for flow limitation extraction`
- `refactor: Simplify EDF signal mapping`

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- List of changes made
- New parsers or features added
- Breaking changes (if any)

## Testing
How was this tested? What test data was used?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
- [ ] No linting errors
- [ ] Sample data anonymized
```

## Style Guide

### Python Style

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints for function signatures
- Write docstrings for public APIs (Google style)

### Example

```python
from typing import List, Optional
from datetime import date

def get_sessions(
    device_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Session]:
    """
    Get therapy sessions with optional filtering.
    
    Args:
        device_id: Device serial number to filter by. If None, returns all devices.
        start_date: Earliest session date to include. If None, no lower bound.
        end_date: Latest session date to include. If None, no upper bound.
    
    Returns:
        List of Session objects matching the filters.
    
    Example:
        >>> reader = CPAPReader("/path/to/sdcard")
        >>> sessions = reader.get_sessions(start_date=date(2025, 11, 1))
        >>> print(f"Found {len(sessions)} sessions")
    """
    # Implementation...
    pass
```

## Documentation

### Updating Documentation

When making changes:

1. Update relevant `.md` files
2. Update docstrings in code
3. Add examples if needed
4. Update README if API changes
5. Add usage examples to USAGE.md

### Documentation Standards

- Use clear, simple language
- Include code examples
- Keep examples up to date
- Use proper Markdown formatting
- Include type hints in code examples

## Community

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and discussions
- **Pull Requests**: For code contributions

### Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes
- Project documentation

## Special Considerations

### Medical Device Data

- Always anonymize patient data
- Follow HIPAA guidelines for data handling
- Never commit identifying information
- Be mindful of data privacy in issues and PRs

### CPAP-Specific Knowledge

Resources for learning about CPAP data:
- [OSCAR project](https://www.sleepfiles.com/OSCAR/)
- [EDF+ specification](https://www.edfplus.info/)
- [ResMed AirView documentation](https://www.resmed.com/)
- [ApneaBoard forums](https://www.apneaboard.com/)

## Questions?

If you have questions about contributing:

1. Check existing issues and discussions
2. Read the documentation
3. Ask in GitHub Discussions
4. Contact maintainers

Thank you for contributing! 🎉
