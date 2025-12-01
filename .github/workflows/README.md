# GitHub Actions Workflows - cpap-py

This directory contains automated CI/CD workflows for the cpap-py project.

## Workflows

### 1. Tests (`tests.yml`)

**Purpose:** Automated testing and code quality checks

**Triggers:**
- Push to `main` branch
- Pull requests to `main`
- Daily at 2am UTC (scheduled)
- Manual workflow dispatch

**Jobs:**

**Test Job:**
- Runs on Ubuntu latest
- Tests against Python 3.9, 3.10, 3.11, and 3.12
- Installs package with `pip install -e ".[dev]"`
- Runs pytest with coverage reporting
- Checks for 95% coverage threshold
- Uploads coverage to Codecov (Python 3.12 only)
- Uploads HTML coverage report as artifact

**Lint Job:**
- Runs on Ubuntu latest with Python 3.12
- Checks code formatting with Black
- Lints code with Ruff
- Performs type checking with MyPy

### 2. Security (`security.yml`)

**Purpose:** Security scanning and vulnerability detection

**Triggers:**
- Push to `main` branch
- Pull requests to `main`
- Weekly on Mondays at 3am UTC
- Manual workflow dispatch

**Jobs:**

**Dependency Scan:**
- Uses Safety to check for vulnerable dependencies
- Generates JSON report for tracking

**Bandit Scan:**
- Scans Python code for security issues
- Uploads security report as artifact (90-day retention)

**CodeQL Analysis:**
- GitHub's semantic code analysis
- Uses security-extended and security-and-quality queries
- Checks for vulnerabilities and code quality issues

**Secret Scan:**
- Uses TruffleHog to detect accidentally committed secrets
- Scans commit history for exposed credentials

### 3. Dependency Updates (`dependency-updates.yml`)

**Purpose:** Monitor and report on dependency updates

**Triggers:**
- Weekly on Mondays at 9am UTC
- Manual workflow dispatch

**Jobs:**

**Update Dependencies:**
- Lists outdated packages
- Runs pip-audit to check for vulnerabilities
- Automatically creates GitHub issue if vulnerabilities are found
- Tags issues with `security` and `dependencies` labels

### 4. Publish to PyPI (`publish-to-pypi.yml`)

**Purpose:** Automated package publishing

**Triggers:**
- When a GitHub release is published
- Manual workflow dispatch

**Jobs:**

**Build and Publish:**
- Builds source and wheel distributions
- Publishes to PyPI using trusted publishing (OIDC)
- Requires PyPI trusted publisher configuration

## Configuration

### Required Secrets

No repository secrets are required if using trusted publishing for PyPI.

### Optional Codecov Integration

To enable Codecov uploads:
1. Sign up at https://codecov.io
2. Add your repository
3. Codecov will automatically detect uploads from GitHub Actions

### PyPI Trusted Publishing Setup

To enable automated PyPI publishing:

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher with:
   - PyPI Project Name: `cpap-py`
   - Owner: `dynacylabs`
   - Repository: `cpap-py`
   - Workflow: `publish-to-pypi.yml`
   - Environment: `pypi`

## Manual Workflow Dispatch

All workflows can be triggered manually:

1. Go to "Actions" tab in GitHub
2. Select the workflow
3. Click "Run workflow"
4. Select the branch and click "Run workflow"

## Viewing Results

### Test Results
- Check the "Actions" tab for test runs
- View coverage reports in the artifacts section
- Coverage trends visible in Codecov (if configured)

### Security Scans
- Review security scan results in the "Actions" tab
- CodeQL results also appear in the "Security" tab
- Download Bandit reports from artifacts

### Dependency Updates
- Check the "Issues" tab for automatically created vulnerability reports
- Review weekly dependency audit logs in "Actions"

## Status Badges

Add these to your README.md:

```markdown
[![Tests](https://github.com/dynacylabs/cpap-py/workflows/Tests/badge.svg)](https://github.com/dynacylabs/cpap-py/actions/workflows/tests.yml)
[![Security](https://github.com/dynacylabs/cpap-py/workflows/Security%20Scanning/badge.svg)](https://github.com/dynacylabs/cpap-py/actions/workflows/security.yml)
```

## Local Testing

Run the same checks locally before pushing:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest tests/ -v --cov=cpap_py --cov-report=term-missing

# Check formatting
black --check src/cpap_py/ tests/

# Lint code
ruff check src/cpap_py/ tests/

# Type check
mypy src/cpap_py/ --ignore-missing-imports

# Security scan
pip install bandit safety
bandit -r src/cpap_py/
safety check
```

## Workflow Maintenance

### Updating Python Versions

Edit the matrix in `tests.yml`:

```yaml
matrix:
  python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']  # Add new versions
```

### Adjusting Coverage Threshold

Edit the coverage check in `tests.yml`:

```yaml
- name: Check coverage threshold
  run: |
    coverage report --fail-under=95  # Change threshold here
```

### Changing Schedule

Edit the cron expressions:

```yaml
schedule:
  - cron: '0 2 * * *'  # Daily at 2am UTC
  # Format: minute hour day month dayofweek
  # Use https://crontab.guru to help
```
