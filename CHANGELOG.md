# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-26

### Added
- Support for Python 3.12, 3.13, and 3.14
- Type checking with mypy in CI pipeline
- Ruff linter and formatter configuration in `pyproject.toml`
- CHANGELOG.md file for tracking version history

### Changed
- **BREAKING**: Minimum Python version increased from 3.7 to 3.10
- Replaced flake8 with ruff for linting and formatting
- Updated GitHub Actions to latest versions:
  - `actions/checkout`: v3 → v6
  - `actions/setup-python`: v5 → v6
  - `suzuki-shunsuke/github-action-renovate-config-validator`: v0.1.3 → v2.0.0
- Updated Renovate config to use `config:recommended` instead of deprecated `config:base`
- Simplified `importlib.metadata` imports (removed backport fallback)
- Applied ruff formatting across entire codebase
- Fixed implicit Optional type annotations for mypy compliance

### Removed
- Support for Python 3.7, 3.8, and 3.9
- `.flake8` configuration file (migrated to `pyproject.toml`)
- ReadTheDocs documentation links (documentation takeover security fix)
- `readthedocs.yml` and `mkdocs.yml` configuration files
- `docs/` directory used for ReadTheDocs generation
- `importlib_metadata` backport dependency

### Security
- Removed links to compromised ReadTheDocs documentation site

## [0.0.3] - Previous Release

- See git history for changes prior to this changelog

