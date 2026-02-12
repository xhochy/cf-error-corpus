# AGENTS.md / CLAUDE.md

This file provides guidance to coding agents when working with code in this repository.

## Project Overview

cf-error-corpus is a curated collection of error logs from conda-forge package builds, packaged as a Python library. The core value is in the `corpus/` directory containing structured error data; the Python package itself is minimal (version detection only).

## Development Environment

This project uses **Pixi** (not pip/conda directly) for dependency management. All commands are run through `pixi run`.

```bash
pixi run postinstall        # Install package in editable mode (run first)
pixi run test               # Run pytest
pixi run test-coverage      # Run pytest with coverage
pixi run pre-commit-run     # Run all linting/formatting checks
pixi run build-wheel        # Build distribution wheel
pixi run check-wheel        # Validate wheel with twine
```

To run a single test: `pixi run test tests/test_core.py::test_name`

**Important:** Whenever you modify `pixi.toml`, always run `pixi lock` to update the lock file (`pixi.lock`). This ensures dependency versions are properly tracked and the environment is reproducible.

## Corpus Data Structure

Error logs live under `corpus/` organized by error category:

```
corpus/<category>/<package>-<build_number>-<timestamp>-<platform-python>/
  ├── error.log    # Full raw build error log
  └── input.yml    # Metadata: source link, minimal error, expected parsed output
```

## Code Quality

- **Python >=3.13** required (strict, not backwards-compatible)
- **Ruff** for linting and formatting (line-length 88, double quotes)
- **Mypy** in strict mode for type checking
- **Prettier** for YAML/Markdown (print width 200, double quotes)
- **Taplo** for TOML formatting
- **Typos** for spell checking (excludes `corpus/` directory)
- Pre-commit hooks enforce all of the above; run `pixi run pre-commit-install` to set up

## Project Structure

- `cf_error_corpus/` — Python package (minimal: just version detection via setuptools-scm)
- `corpus/` — The actual error log dataset, organized by error category
- `tests/` — pytest test suite
- `pixi.toml` — Task definitions and dependency management (multiple environments: default, py313, build, lint)
