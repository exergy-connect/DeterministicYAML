"""
Tests for dyaml convert command.
"""

import pytest
import tempfile
import os
from pathlib import Path
from dyaml.cli.convert import _convert_single_file
from dyaml.core.parser import parse_yaml_string_with_comments
from dyaml.core.converter import convert_yaml_to_deterministic
from dyaml.core.serializer import to_deterministic_yaml


def test_convert_preserves_comments():
    """Test that convert preserves comments as $human$ fields."""
    yaml_input = """# Production config
database:
  # Primary database
  host: db.example.com
  port: 5432
"""
    
    data, comments = parse_yaml_string_with_comments(yaml_input)
    deterministic_data = convert_yaml_to_deterministic(data, comments, preserve_comments=True)
    output = to_deterministic_yaml(deterministic_data)
    
    assert '$human$' in output
    assert 'Production config' in output and 'Primary database' in output


def test_convert_consolidates_multiple_comments():
    """Test that multiple comments are consolidated."""
    yaml_input = """# Comment 1
# Comment 2
service:
  name: auth
  # Comment 3
  retries: 3  # Comment 4
"""
    
    data, comments = parse_yaml_string_with_comments(yaml_input)
    deterministic_data = convert_yaml_to_deterministic(data, comments, preserve_comments=True)
    output = to_deterministic_yaml(deterministic_data)
    
    # Should have $human$ field with all comments consolidated
    assert '$human$' in output
    assert 'Comment 1' in output
    assert 'Comment 2' in output
    assert 'Comment 3' in output
    assert 'Comment 4' in output
    # Verify they're consolidated with | delimiter (4 comments = 3 delimiters)
    assert output.count('|') == 3


def test_convert_strips_comments_when_requested():
    """Test that comments are stripped when preserve_comments=False."""
    yaml_input = """# Comment
name: John
age: 30
"""
    
    data, comments = parse_yaml_string_with_comments(yaml_input)
    deterministic_data = convert_yaml_to_deterministic(data, comments, preserve_comments=False)
    output = to_deterministic_yaml(deterministic_data)
    
    # Should not have $human$ field or comment text
    assert '$human$' not in output
    assert 'Comment' not in output
    # Should preserve actual data
    assert 'name: John' in output
    assert 'age: 30' in output


def test_convert_idempotent():
    """Test that convert(convert(x)) == convert(x)."""
    yaml_input = """name: John
age: 30
active: true
"""
    
    # First conversion
    data1, comments1 = parse_yaml_string_with_comments(yaml_input)
    det1 = convert_yaml_to_deterministic(data1, comments1, preserve_comments=True)
    output1 = to_deterministic_yaml(det1)
    
    # Second conversion (should be same)
    data2, comments2 = parse_yaml_string_with_comments(output1)
    det2 = convert_yaml_to_deterministic(data2, comments2, preserve_comments=True)
    output2 = to_deterministic_yaml(det2)
    
    # Should be identical (or at least semantically equivalent)
    assert output1.strip() == output2.strip()


def test_convert_handles_nested_structures():
    """Test conversion with nested dictionaries and lists."""
    yaml_input = """database:
  hosts:
    - primary
    - secondary
  config:
    timeout: 30
"""
    
    data, comments = parse_yaml_string_with_comments(yaml_input)
    deterministic_data = convert_yaml_to_deterministic(data, comments, preserve_comments=True)
    output = to_deterministic_yaml(deterministic_data)
    
    # Verify all keys are present
    assert 'database:' in output
    assert 'hosts:' in output
    assert 'config:' in output
    # Verify list items are present
    assert '- primary' in output
    assert '- secondary' in output
    # Verify nested value
    assert 'timeout: 30' in output

