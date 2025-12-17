# Contributing to cpap-py

Thank you for your interest in contributing to cpap-py! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project follows a simple code of conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences
- Accept responsibility and apologize for mistakes

## How Can I Contribute?

### Types of Contributions

We welcome many types of contributions:

- **Bug fixes** - Fix issues in the code
- **New features** - Add new functionality
- **Documentation** - Improve README, guides, or code comments
- **Tests** - Add or improve test coverage
- **Performance** - Optimize code performance
- **Code quality** - Refactoring, type hints, etc.
- **Examples** - Add usage examples

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- pip
- Virtual environment tool (venv, virtualenv, or conda)

### Setup Instructions

1. **Fork and Clone**

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/cpap-py.git
cd cpap-py
```

2. **Add Upstream Remote**

```bash
git remote add upstream https://github.com/dynacylabs/cpap-py.git
```

3. **Create Virtual Environment**

```bash
# Using venv (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Using conda
conda create -n cpap-py python=3.11
conda activate cpap-py
```

4. **Install Development Dependencies**

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"
```

5. **Verify Installation**

```bash
# Run tests to verify setup
./run_tests.sh

# Check imports
python -c "from cpap_py import CPAPLoader; print('Success!')"
```

## Development Workflow

### 1. Sync with Upstream

Before starting work, sync with the main repository:

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/what-changed` - Documentation updates
- `refactor/what-changed` - Code refactoring
- `test/what-added` - Test additions

### 3. Make Changes

- Write clear, focused commits
- Add tests for new functionality
- Update documentation as needed
- Follow coding standards

### 4. Test Your Changes

```bash
# Run full test suite
./run_tests.sh

# Run specific tests
pytest tests/test_your_file.py -v

# Check coverage
pytest tests/ --cov=cpap_py --cov-report=term-missing
```

### 5. Commit and Push

```bash
git add .
git commit -m "Add feature: brief description

Longer description of what changed and why.
Reference issues if applicable (#123)."
git push origin feature/your-feature-name
```

### 6. Create Pull Request

Open a Pull Request on GitHub with a clear description of your changes.

## Coding Standards

### Python Style Guide

We follow PEP 8 with these guidelines:

- **Line length**: 100 characters
- **Quotes**: Use double quotes for strings
- **Imports**: Group and sort (stdlib, third-party, local)
- **Type hints**: Use for function signatures
- **Docstrings**: Use Google-style docstrings

### Code Formatting

Use **Black** for code formatting:

```bash
black src/ tests/
```

### Linting

Use **Ruff** for linting:

```bash
ruff check src/ tests/
```

## Testing Guidelines

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Aim to maintain 95%+ code coverage
- Tests should be clear and independent

### Running Tests

```bash
# Run all tests
./run_tests.sh

# Run specific test file
pytest tests/test_identification.py -v

# Run with coverage
pytest tests/ --cov=cpap_py --cov-report=term-missing
```

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Commit messages are clear

### PR Description

Include:
- Description of changes
- Type of change (bug fix, feature, docs, etc.)
- How you tested the changes
- Related issues (if applicable)

### Review Process

1. Automated checks will run
2. Maintainers will review your code
3. Address any feedback
4. Once approved, PR will be merged

## Reporting Bugs

Use the GitHub issue tracker to report bugs. Include:

- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Error messages/stack traces

## Suggesting Enhancements

We welcome enhancement suggestions! Open an issue with:

- Clear feature description
- Use case / why it's needed
- Proposed solution
- Alternative approaches considered

## Questions?

- Open an issue on GitHub
- Check DEVELOPMENT.md for more details
- Review existing issues and discussions

## Thank You!

Thank you for contributing to cpap-py! Every contribution helps make CPAP data analysis more accessible.

