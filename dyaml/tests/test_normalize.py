"""
Tests for dyaml normalize command.
"""

import pytest
from dyaml.core.parser import parse_yaml_string_with_comments
from dyaml.core.converter import convert_yaml_to_deterministic
from dyaml.core.serializer import to_deterministic_yaml


def test_normalize_sorts_keys():
    """Test that normalize sorts keys lexicographically."""
    yaml_input = """zebra: last
apple: first
banana: middle
"""
    
    data, comments = parse_yaml_string_with_comments(yaml_input)
    deterministic_data = convert_yaml_to_deterministic(data, comments, preserve_comments=True)
    output = to_deterministic_yaml(deterministic_data)
    
    # Keys should be sorted: apple, banana, zebra
    apple_pos = output.find('apple:')
    banana_pos = output.find('banana:')
    zebra_pos = output.find('zebra:')
    
    # Ordering implies all keys exist (find returns -1 if not found)
    assert apple_pos < banana_pos < zebra_pos
    # Verify values are preserved
    assert 'first' in output
    assert 'middle' in output
    assert 'last' in output


def test_normalize_positions_human_first():
    """Test that $human$ field is positioned first."""
    yaml_input = """name: John
$human$: User profile
age: 30
"""
    
    data, comments = parse_yaml_string_with_comments(yaml_input)
    deterministic_data = convert_yaml_to_deterministic(data, comments, preserve_comments=True)
    output = to_deterministic_yaml(deterministic_data)
    
    # $human$ should appear before other keys (which are sorted: age, name)
    human_pos = output.find('$human$:')
    age_pos = output.find('age:')
    name_pos = output.find('name:')
    
    # Verify $human$ exists and is first (ordering implies age and name exist)
    assert human_pos >= 0, "$human$ field should be present"
    assert human_pos < age_pos < name_pos
    # Verify $human$ value is preserved
    assert 'User profile' in output


def test_normalize_idempotent():
    """Test that normalize(normalize(x)) == normalize(x)."""
    yaml_input = """name: John
age: 30
active: true
"""
    
    # First normalization
    data1, comments1 = parse_yaml_string_with_comments(yaml_input)
    det1 = convert_yaml_to_deterministic(data1, comments1, preserve_comments=True)
    output1 = to_deterministic_yaml(det1)
    
    # Second normalization
    data2, comments2 = parse_yaml_string_with_comments(output1)
    det2 = convert_yaml_to_deterministic(data2, comments2, preserve_comments=True)
    output2 = to_deterministic_yaml(det2)
    
    # Should be identical
    assert output1.strip() == output2.strip()


def test_normalize_preserves_human_fields():
    """Test that normalize preserves $human$ fields."""
    yaml_input = """$human$: User profile
name: John
age: 30
"""
    
    data, comments = parse_yaml_string_with_comments(yaml_input)
    deterministic_data = convert_yaml_to_deterministic(data, comments, preserve_comments=True)
    output = to_deterministic_yaml(deterministic_data)
    
    assert '$human$' in output
    assert 'User profile' in output

