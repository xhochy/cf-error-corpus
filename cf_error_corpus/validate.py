"""Validate input.yml files in the corpus directory."""

import sys
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, Field, HttpUrl, ValidationError


class InputYaml(BaseModel):
    """Schema for input.yml files in the corpus."""

    source: Annotated[HttpUrl, Field(description="URL to the source issue or PR")]
    input: Annotated[
        str, Field(description="Reference to the error log file", pattern=r"^error\.log$")
    ]
    most_minimal_output: Annotated[
        str, Field(description="Most minimal error output", min_length=1)
    ]
    expected_output: Annotated[
        str, Field(description="Expected full error output", min_length=1)
    ]


def validate_input_yml(file_path: Path) -> tuple[bool, str]:
    """
    Validate a single input.yml file.

    Args:
        file_path: Path to the input.yml file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)

        InputYaml.model_validate(data)
        return True, ""
    except ValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error reading file: {e}"


def main() -> int:
    """
    Main CLI entry point to validate all input.yml files in corpus/.

    Returns:
        Exit code (0 for success, 1 for validation errors)
    """
    corpus_dir = Path(__file__).parent.parent / "corpus"

    if not corpus_dir.exists():
        print(f"Error: corpus directory not found at {corpus_dir}", file=sys.stderr)
        return 1

    input_files = list(corpus_dir.rglob("input.yml"))

    if not input_files:
        print("Warning: No input.yml files found in corpus/", file=sys.stderr)
        return 0

    errors = []
    for input_file in sorted(input_files):
        is_valid, error_msg = validate_input_yml(input_file)
        if not is_valid:
            relative_path = input_file.relative_to(corpus_dir.parent)
            errors.append(f"\n{relative_path}:\n{error_msg}")

    if errors:
        print("Validation errors found:", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"✓ All {len(input_files)} input.yml files are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
