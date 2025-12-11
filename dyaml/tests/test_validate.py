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
    # Should have specific error about comments on line 1
    comment_errors = [e for e in result.errors if 'comment' in e.message.lower()]
    assert len(comment_errors) > 0 and any(e.line == 1 for e in comment_errors), "Should have comment-related error on line 1"


def test_validate_rejects_flow_style():
    """Test that flow style is rejected."""
    invalid_yaml = """config: {key: value}
"""
    
    result = validate_string(invalid_yaml)
    # Flow style should be rejected
    assert not result.valid
    # Should have error about flow style
    flow_errors = [e for e in result.errors if 'flow' in e.message.lower()]
    assert len(flow_errors) > 0, "Should have flow style error"


def test_validate_checks_indentation():
    """Test that tabs are rejected."""
    invalid_yaml = """name:\tJohn
age: 30
"""
    
    result = validate_string(invalid_yaml)
    assert not result.valid
    # Should have specific error about tabs
    tab_errors = [e for e in result.errors if 'tab' in e.message.lower()]
    assert len(tab_errors) > 0, "Should have tab-related error"
    # Error should be on line 1 where the tab is
    assert any(e.line == 1 for e in tab_errors), "Tab error should be on line 1"

