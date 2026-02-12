# cf-error-corpus

[![CI](https://img.shields.io/github/actions/workflow/status/xhochy/cf-error-corpus/ci.yml?style=flat-square&branch=main)](https://github.com/xhochy/cf-error-corpus/actions/workflows/ci.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/cf-error-corpus?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/cf-error-corpus)
[![pypi-version](https://img.shields.io/pypi/v/cf-error-corpus.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/cf-error-corpus)
[![python-version](https://img.shields.io/pypi/pyversions/cf-error-corpus?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/cf-error-corpus)

A collection of error logs from builds on conda-forge

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
