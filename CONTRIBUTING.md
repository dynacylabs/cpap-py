# Contributing to CPAP Data Parser

Thank you for your interest in contributing!

## Quick Start

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-new-feature`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to the branch: `git push origin feature/my-new-feature`
7. Submit a pull request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/dynacylabs/cpap_analysis.git
cd cpap_analysis

# Install in development mode
pip install -e .

# Run example
python dump_cpap_data.py data/set_1/ > output.json
```

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose

## Testing

Add tests for new functionality in the `tests/` directory.

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the DATA_GUIDE.md if you add new data fields
3. The PR will be merged once reviewed and approved

## Questions?

Open an issue or reach out to the maintainers.
