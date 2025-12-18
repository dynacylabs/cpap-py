"""
cpap-py Setup
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')
else:
    long_description = "A comprehensive Python library for parsing and analyzing ResMed CPAP machine data"

setup(
    name="cpap-py",
    author="DynacyLabs",
    description="A comprehensive Python library for parsing and analyzing ResMed CPAP machine data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dynacylabs/cpap-py",
    project_urls={
        "Homepage": "https://github.com/dynacylabs/cpap-py",
        "Documentation": "https://github.com/dynacylabs/cpap-py",
        "Repository": "https://github.com/dynacylabs/cpap-py",
        "Issues": "https://github.com/dynacylabs/cpap-py/issues",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "coverage>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "coverage>=7.0.0",
        ],
    },
)
