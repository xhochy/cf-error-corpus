"""Tests for the CLI module."""

import pytest

from cf_error_corpus.cli import (
    extract_build_name_from_check_run_name,
    find_failed_azure_builds,
    parse_azure_details_url,
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


def test_parse_azure_details_url() -> None:
    """Test parsing Azure Pipelines details URLs."""
    url = (
        "https://dev.azure.com/conda-forge/84710dde-1620-425b-80d0-4cf5baca359d"
        "/_build/results?buildId=1460232&view=logs"
        "&jobId=7b6f2c87-f3a7-5133-8d84-7c03a75d9dfc"
    )
    result = parse_azure_details_url(url)
    assert result is not None
    org, project, build_id, job_id = result
    assert org == "conda-forge"
    assert project == "84710dde-1620-425b-80d0-4cf5baca359d"
    assert build_id == "1460232"
    assert job_id == "7b6f2c87-f3a7-5133-8d84-7c03a75d9dfc"


def test_parse_azure_details_url_no_job_id() -> None:
    """Test parsing Azure Pipelines URL without jobId."""
    url = (
        "https://dev.azure.com/conda-forge/myproject"
        "/_build/results?buildId=12345&view=logs"
    )
    result = parse_azure_details_url(url)
    assert result is not None
    org, project, build_id, job_id = result
    assert org == "conda-forge"
    assert project == "myproject"
    assert build_id == "12345"
    assert job_id is None


def test_parse_azure_details_url_invalid() -> None:
    """Test parsing invalid Azure Pipelines URLs."""
    assert parse_azure_details_url("https://example.com/foo") is None
    assert (
        parse_azure_details_url("https://dev.azure.com/org/proj/_build/results") is None
    )
