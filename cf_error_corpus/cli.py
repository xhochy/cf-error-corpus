"""CLI for downloading Azure Pipeline logs from conda-forge PRs."""

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import click


def parse_github_pr_url(url: str) -> tuple[str, str, int]:
    """Parse GitHub PR URL to extract owner, repo, and PR number.

    Args:
        url: GitHub PR URL (e.g., https://github.com/conda-forge/nomad-feedstock/pull/52)

    Returns:
        Tuple of (owner, repo, pr_number)

    Raises:
        ValueError: If URL format is invalid
    """
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise ValueError(
            f"Invalid GitHub PR URL: {url}. "
            "Expected format: https://github.com/owner/repo/pull/number"
        )
    owner, repo, pr_str = match.groups()
    return owner, repo, int(pr_str)


def get_pr_info_from_api(owner: str, repo: str, pr_number: int) -> dict[str, Any]:
    """Get PR information from GitHub API.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number

    Returns:
        PR information dictionary

    Raises:
        urllib.error.HTTPError: If API request fails
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")

    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())


def get_commit_check_runs_from_api(
    owner: str, repo: str, sha: str
) -> list[dict[str, Any]]:
    """Get check runs for a commit from GitHub API.

    Args:
        owner: Repository owner
        repo: Repository name
        sha: Commit SHA

    Returns:
        List of check run dictionaries

    Raises:
        urllib.error.HTTPError: If API request fails
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}/check-runs"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        return data.get("check_runs", [])


def download_content(url: str) -> str:
    """Download content from a URL.

    Args:
        url: URL to download from

    Returns:
        Content as string

    Raises:
        urllib.error.HTTPError: If download fails
    """
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8", errors="replace")


def create_corpus_entry(
    output_dir: Path,
    feedstock_name: str,
    pr_number: int,
    build_name: str,
    log_content: str,
    pr_url: str,
) -> Path:
    """Create a corpus entry with error.log and input.yml.

    Args:
        output_dir: Base output directory for corpus entries
        feedstock_name: Name of the feedstock (without -feedstock suffix)
        pr_number: PR number
        build_name: Build name (e.g., linux_64, osx_64)
        log_content: Full log content
        pr_url: GitHub PR URL for the source field

    Returns:
        Path to created directory
    """
    # Create folder name: feedstock-pr-buildname
    folder_name = f"{feedstock_name}-{pr_number}-{build_name}"
    entry_dir = output_dir / folder_name
    entry_dir.mkdir(parents=True, exist_ok=True)

    # Write error.log
    error_log_path = entry_dir / "error.log"
    error_log_path.write_text(log_content, encoding="utf-8")

    # Create input.yml
    input_yml_path = entry_dir / "input.yml"
    input_yml_content = f"""source: {pr_url}
input: error.log
most_minimal_output: |
  # TODO: Fill in the minimal error message
expected_output: |
  # TODO: Fill in the expected parsed output
"""
    input_yml_path.write_text(input_yml_content, encoding="utf-8")

    return entry_dir


def extract_build_name_from_check_run_name(name: str, arch: str) -> str:
    """Extract build name from check run name.

    Args:
        name: Check run name
        arch: Architecture hint (linux or osx)

    Returns:
        Build name (e.g., linux_64, osx_arm64)
    """
    name_lower = name.lower()

    if arch == "linux":
        if "aarch64" in name_lower or "arm64" in name_lower:
            return "linux_aarch64"
        return "linux_64"
    elif arch == "osx":
        if "arm64" in name_lower or "aarch64" in name_lower:
            return "osx_arm64"
        return "osx_64"

    return arch


def find_failed_azure_builds(
    check_runs: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Find first failed Azure build for each architecture (linux and osx).

    Args:
        check_runs: List of check runs from GitHub API

    Returns:
        Dictionary mapping architecture to check run info
    """
    failed_builds: dict[str, dict[str, Any]] = {}

    for run in check_runs:
        # Look for Azure Pipelines check runs that failed
        if run.get("conclusion") != "failure":
            continue

        if run.get("app", {}).get("slug") != "azure-pipelines":
            continue

        name = run.get("name", "")

        # Check for linux builds
        if "linux" in name.lower() and "linux" not in failed_builds:
            failed_builds["linux"] = run

        # Check for osx/macos builds
        if (
            "osx" in name.lower() or "macos" in name.lower()
        ) and "osx" not in failed_builds:
            failed_builds["osx"] = run

        # Stop if we found both
        if len(failed_builds) >= 2:
            break

    return failed_builds


def extract_azure_log_url_from_details(details_url: str) -> str | None:
    """Try to extract Azure Pipelines log URL from details page.

    Args:
        details_url: Azure Pipelines details URL

    Returns:
        Log URL if found, None otherwise
    """
    # Parse Azure Pipelines URL to construct log URL
    # Format: https://dev.azure.com/{org}/{project}/_build/results?buildId={buildId}&view=logs&j={jobId}&t={taskId}
    # Log URL: https://dev.azure.com/{org}/{project}/_apis/build/builds/{buildId}/logs/{logId}

    match = re.search(r"buildId=(\d+)", details_url)
    if not match:
        return None

    build_id = match.group(1)

    # Extract organization and project from URL
    match = re.match(r"https://dev\.azure\.com/([^/]+)/([^/]+)/_build", details_url)
    if not match:
        return None

    org, project = match.groups()

    # Try to get the logs via API
    # First get list of logs for the build
    api_url = (
        f"https://dev.azure.com/{org}/{project}/_apis/build/builds/{build_id}/logs"
    )
    return api_url


def get_azure_build_logs(api_url: str) -> str | None:
    """Get full build logs from Azure Pipelines.

    Args:
        api_url: Azure Pipelines API URL for logs list

    Returns:
        Combined log content, or None if unable to fetch
    """
    try:
        # Get list of logs
        req = urllib.request.Request(api_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())

        logs_content = []

        # Download each log
        for log in data.get("value", []):
            log_url = log.get("url")
            if log_url:
                try:
                    log_content = download_content(log_url)
                    logs_content.append(log_content)
                except Exception:
                    # Skip logs we can't download
                    continue

        if logs_content:
            return "\n".join(logs_content)

    except Exception:
        return None

    return None


@click.command()
@click.argument("pr_url")
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("corpus"),
    help="Output directory for corpus entries (default: corpus)",
)
@click.option(
    "-c",
    "--category",
    default="uncategorized",
    help="Category subdirectory for corpus entries (default: uncategorized)",
)
def main(pr_url: str, output_dir: Path, category: str) -> int:
    """Download Azure Pipeline logs from conda-forge PRs.

    PR_URL: GitHub PR URL (e.g., https://github.com/conda-forge/nomad-feedstock/pull/52)
    """
    try:
        # Parse PR URL
        owner, repo, pr_number = parse_github_pr_url(pr_url)
        click.echo(f"Fetching PR info for {owner}/{repo}#{pr_number}...")

        # Get PR info
        pr_info = get_pr_info_from_api(owner, repo, pr_number)
        head_sha = pr_info["head"]["sha"]
        click.echo(f"Head commit: {head_sha}")

        # Get check runs
        click.echo("Fetching check runs...")
        check_runs = get_commit_check_runs_from_api(owner, repo, head_sha)

        # Find failed builds
        failed_builds = find_failed_azure_builds(check_runs)

        if not failed_builds:
            click.echo("No failed Azure Pipeline builds found for this PR.")
            return 1

        click.echo(
            f"Found {len(failed_builds)} failed build(s): {', '.join(failed_builds.keys())}"
        )

        # Extract feedstock name (remove -feedstock suffix if present)
        feedstock_name = repo.replace("-feedstock", "")

        # Create output directory
        output_base = output_dir / category
        output_base.mkdir(parents=True, exist_ok=True)

        # Download logs for each failed build
        for arch, run_info in failed_builds.items():
            click.echo(f"\nProcessing {arch} build: {run_info['name']}")

            # Extract build name from check run name
            build_name = extract_build_name_from_check_run_name(run_info["name"], arch)

            click.echo(f"  Build name: {build_name}")

            # Get details URL
            details_url = run_info.get("details_url", "")
            if not details_url:
                click.echo(f"  Warning: No details URL found for {arch} build")
                continue

            click.echo(f"  Details URL: {details_url}")

            # Try to get log URL
            log_api_url = extract_azure_log_url_from_details(details_url)

            if log_api_url:
                click.echo("  Attempting to download logs from Azure API...")
                log_content = get_azure_build_logs(log_api_url)

                if log_content:
                    click.echo(
                        f"  Successfully downloaded logs ({len(log_content)} bytes)"
                    )
                else:
                    click.echo("  Warning: Could not download logs from Azure API")
                    log_content = (
                        f"# Could not download logs automatically\n"
                        f"# Azure details URL: {details_url}\n"
                        f"# Please download manually\n"
                    )
            else:
                click.echo("  Warning: Could not parse Azure log URL")
                log_content = (
                    f"# Could not parse Azure log URL\n"
                    f"# Azure details URL: {details_url}\n"
                    f"# Please download manually\n"
                )

            # Create entry directory
            entry_dir = create_corpus_entry(
                output_base,
                feedstock_name,
                pr_number,
                build_name,
                log_content,
                pr_url,
            )
            click.echo(f"  Created entry directory: {entry_dir}")

        click.echo("\nDone!")
        return 0

    except urllib.error.HTTPError as e:
        click.echo(f"HTTP Error: {e.code} - {e.reason}", err=True)
        if e.code == 403:
            click.echo(
                "Note: GitHub API rate limit may be exceeded. "
                "Consider using a GitHub token.",
                err=True,
            )
        return 1
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
