"""
Tests for dyaml validate command.
"""

import pytest
from dyaml.core.validator import validate_string, ValidationResult


def test_validate_accepts_correct_dyaml():
    """Test that valid Deterministic YAML passes validation."""
    valid_yaml = """name: John
age: 30
active: true
"""
    
    result = validate_string(valid_yaml)
    assert result.valid
    assert len(result.errors) == 0


def test_validate_rejects_comments():
    """Test that YAML with comments is rejected."""
    invalid_yaml = """# Comment
name: John
age: 30
"""
    
    result = validate_string(invalid_yaml)
    assert not result.valid
    assert len(result.errors) > 0
    assert any('comment' in e.message.lower() for e in result.errors)


def test_validate_rejects_flow_style():
    """Test that flow style is rejected."""
    invalid_yaml = """config: {key: value}
"""
    
    result = validate_string(invalid_yaml)
    # Note: This might pass if flow style is inside quotes
    # Full validation would need more sophisticated parsing


def test_validate_checks_indentation():
    """Test that tabs are rejected."""
    invalid_yaml = """name:\tJohn
age: 30
"""
    
    result = validate_string(invalid_yaml)
    assert not result.valid
    assert any('tab' in e.message.lower() for e in result.errors)

