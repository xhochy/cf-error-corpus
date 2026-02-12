"""Tests for the CLI module."""

import pytest

from cf_error_corpus.cli import (
    extract_build_name_from_check_run_name,
    find_failed_azure_builds,
    parse_github_pr_url,
)


def test_parse_github_pr_url() -> None:
    """Test parsing GitHub PR URLs."""
    owner, repo, pr_number = parse_github_pr_url(
        "https://github.com/conda-forge/nomad-feedstock/pull/52"
    )
    assert owner == "conda-forge"
    assert repo == "nomad-feedstock"
    assert pr_number == 52


def test_parse_github_pr_url_invalid() -> None:
    """Test parsing invalid GitHub PR URLs."""
    with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
        parse_github_pr_url("https://github.com/conda-forge/nomad-feedstock")

    with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
        parse_github_pr_url("not a url")


def test_extract_build_name_from_check_run_name() -> None:
    """Test extracting build names from check run names."""
    assert extract_build_name_from_check_run_name("linux_64", "linux") == "linux_64"
    assert (
        extract_build_name_from_check_run_name("linux-aarch64", "linux")
        == "linux_aarch64"
    )
    assert extract_build_name_from_check_run_name("osx_64", "osx") == "osx_64"
    assert extract_build_name_from_check_run_name("osx-arm64", "osx") == "osx_arm64"


def test_find_failed_azure_builds() -> None:
    """Test finding failed Azure builds."""
    check_runs = [
        {
            "name": "linux_64",
            "conclusion": "failure",
            "app": {"slug": "azure-pipelines"},
        },
        {
            "name": "osx_64",
            "conclusion": "failure",
            "app": {"slug": "azure-pipelines"},
        },
        {
            "name": "other",
            "conclusion": "success",
            "app": {"slug": "azure-pipelines"},
        },
        {
            "name": "not-azure",
            "conclusion": "failure",
            "app": {"slug": "other-ci"},
        },
    ]

    failed_builds = find_failed_azure_builds(check_runs)

    assert len(failed_builds) == 2
    assert "linux" in failed_builds
    assert "osx" in failed_builds
    assert failed_builds["linux"]["name"] == "linux_64"
    assert failed_builds["osx"]["name"] == "osx_64"


def test_find_failed_azure_builds_only_linux() -> None:
    """Test finding failed Azure builds with only Linux failures."""
    check_runs = [
        {
            "name": "linux_64",
            "conclusion": "failure",
            "app": {"slug": "azure-pipelines"},
        },
        {
            "name": "osx_64",
            "conclusion": "success",
            "app": {"slug": "azure-pipelines"},
        },
    ]

    failed_builds = find_failed_azure_builds(check_runs)

    assert len(failed_builds) == 1
    assert "linux" in failed_builds
    assert "osx" not in failed_builds
