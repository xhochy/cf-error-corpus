# cf-error-corpus

[![CI](https://img.shields.io/github/actions/workflow/status/xhochy/cf-error-corpus/ci.yml?style=flat-square&branch=main)](https://github.com/xhochy/cf-error-corpus/actions/workflows/ci.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/cf-error-corpus?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/cf-error-corpus)
[![pypi-version](https://img.shields.io/pypi/v/cf-error-corpus.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/cf-error-corpus)
[![python-version](https://img.shields.io/pypi/pyversions/cf-error-corpus?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/cf-error-corpus)

A collection of error logs from builds on conda-forge

## Usage

### Downloading Azure Pipeline Logs

You can download Azure Pipeline logs from conda-forge PRs using the CLI:

```bash
pixi run python -m cf_error_corpus.cli "https://github.com/conda-forge/nomad-feedstock/pull/52" -o corpus -c uncategorized
```

Or after installation:

```bash
cf-error-corpus-download "https://github.com/conda-forge/nomad-feedstock/pull/52" -o corpus -c uncategorized
```

This will:

1. Fetch the PR information from GitHub
2. Find the first failed Linux and OSX builds from Azure Pipelines
3. Attempt to download the full build logs
4. Create directories named `<feedstock>-<pr-number>-<build-name>` (e.g., `nomad-52-linux_64`)
5. Generate `error.log` files with the full build logs
6. Create `input.yml` files with the source PR URL pre-filled

**Options:**

- `-o, --output-dir`: Output directory for corpus entries (default: `corpus`)
- `-c, --category`: Category subdirectory for corpus entries (default: `uncategorized`)

**Note:** Azure Pipelines API access may require authentication for some logs. If automatic download fails, the CLI will provide the Azure Pipelines URL for manual download.

## Installation

This project is managed by [pixi](https://pixi.sh).
You can install the package in development mode using:

```bash
git clone https://github.com/xhochy/cf-error-corpus
cd cf-error-corpus

pixi run pre-commit-install
pixi run postinstall
pixi run test
```
