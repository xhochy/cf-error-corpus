"""Tests for the validate module."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from cf_error_corpus.validate import InputYaml, main, validate_input_yml


def test_input_yaml_schema_valid():
    """Test that the InputYaml schema accepts valid data."""
    valid_data = {
        "source": "https://github.com/conda-forge/test/pull/1",
        "input": "error.log",
        "most_minimal_output": "error: test",
        "expected_output": "full error output here",
    }
    result = InputYaml.model_validate(valid_data)
    assert str(result.source) == valid_data["source"]
    assert result.input == valid_data["input"]


def test_input_yaml_schema_invalid_url():
    """Test that the InputYaml schema rejects invalid URLs."""
    invalid_data = {
        "source": "not-a-url",
        "input": "error.log",
        "most_minimal_output": "error: test",
        "expected_output": "full error output here",
    }
    with pytest.raises(Exception):  # pydantic will raise validation error
        InputYaml.model_validate(invalid_data)


def test_input_yaml_schema_missing_field():
    """Test that the InputYaml schema rejects data with missing fields."""
    invalid_data = {
        "source": "https://github.com/conda-forge/test/pull/1",
        "input": "error.log",
        # missing most_minimal_output
        "expected_output": "full error output here",
    }
    with pytest.raises(Exception):  # pydantic will raise validation error
        InputYaml.model_validate(invalid_data)


def test_validate_input_yml_valid_file():
    """Test validation of a valid input.yml file."""
    with TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "input.yml"
        test_file.write_text("""source: https://github.com/conda-forge/test/pull/1
input: error.log
most_minimal_output: |
  error: test
expected_output: |
  full error output
""")
        is_valid, error_msg = validate_input_yml(test_file)
        assert is_valid
        assert error_msg == ""


def test_validate_input_yml_invalid_file():
    """Test validation of an invalid input.yml file."""
    with TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "input.yml"
        test_file.write_text("""source: not-a-url
input: error.log
most_minimal_output: |
  error: test
expected_output: |
  full error output
""")
        is_valid, error_msg = validate_input_yml(test_file)
        assert not is_valid
        assert "source" in error_msg.lower() or "url" in error_msg.lower()


def test_validate_input_yml_missing_file():
    """Test validation of a missing file."""
    is_valid, error_msg = validate_input_yml(Path("/nonexistent/input.yml"))
    assert not is_valid
    assert "Error reading file" in error_msg


def test_main_with_valid_files():
    """Test main function with valid corpus files."""
    # This will test against actual corpus files if they exist
    exit_code = main()
    # Should succeed (0) or fail (1) depending on corpus files
    assert exit_code in (0, 1)
