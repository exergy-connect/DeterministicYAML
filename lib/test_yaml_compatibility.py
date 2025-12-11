"""
Test that Deterministic YAML is valid YAML.

Deterministic YAML is a subset of standard YAML, so any YAML parser
should be able to parse it correctly.

Copyright (c) 2025 Exergy ∞ LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import yaml
from deterministic_yaml import DeterministicYAML
from deterministic_yaml_parser import parse_deterministic_yaml


def test_yaml_compatibility():
    """Test that Deterministic YAML can be parsed by standard YAML parsers."""
    print("=" * 80)
    print("YAML COMPATIBILITY TEST")
    print("=" * 80)
    print("\nTesting that Deterministic YAML is valid YAML (parsable by PyYAML)...\n")
    
    test_cases = [
        {
            'name': 'Simple mapping',
            'data': {'name': 'John', 'age': 30, 'active': True}
        },
        {
            'name': 'Nested mapping',
            'data': {
                'config': {
                    'host': 'localhost',
                    'port': 5432
                }
            }
        },
        {
            'name': 'List',
            'data': {'tags': ['dev', 'ops', 'important']}
        },
        {
            'name': 'Mixed structure',
            'data': {
                'name': 'John',
                'age': 30,
                'active': True,
                'tags': ['important', 'urgent'],
                'config': {
                    'host': 'localhost',
                    'port': 5432
                }
            }
        },
        {
            'name': 'With quoted strings',
            'data': {
                'description': 'A string with spaces',
                'path': '/usr/local/bin',
                'empty': ''
            }
        },
        {
            'name': 'With null and booleans',
            'data': {
                'value': None,
                'active': True,
                'inactive': False
            }
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        data = test_case['data']
        
        # Generate Deterministic YAML
        deterministic_yaml = DeterministicYAML.to_deterministic_yaml(data)
        
        print(f"  Deterministic YAML:")
        print(f"  {deterministic_yaml.replace(chr(10), chr(10) + '  ')}")
        
        # Try to parse with PyYAML
        parsed_by_pyyaml = yaml.safe_load(deterministic_yaml)
        print(f"  ✓ Parsed by PyYAML: {parsed_by_pyyaml}")
        
        # Verify data equivalence
        assert parsed_by_pyyaml == data, f"Data mismatch for {test_case['name']}: original={data}, parsed={parsed_by_pyyaml}"
        print(f"  ✓ Data matches original")
        
        # Also test with our custom parser
        parsed_by_custom = parse_deterministic_yaml(deterministic_yaml)
        assert parsed_by_custom == data, f"Custom parser mismatch for {test_case['name']}: original={data}, parsed={parsed_by_custom}"
        print(f"  ✓ Parsed by custom parser: matches")
        
        print()
    
    print("=" * 80)
    print("✓ ALL TESTS PASSED")
    print("\nDeterministic YAML is fully compatible with standard YAML parsers!")
    print("=" * 80)


def test_round_trip():
    """Test round-trip: data -> Deterministic YAML -> parse -> same data."""
    print("\n" + "=" * 80)
    print("ROUND-TRIP TEST")
    print("=" * 80)
    print("\nTesting round-trip through Deterministic YAML...\n")
    
    test_data = {
        'name': 'John',
        'age': 30,
        'active': True,
        'tags': ['dev', 'ops'],
        'config': {
            'host': 'localhost',
            'port': 5432
        }
    }
    
    # Generate Deterministic YAML
    deterministic_yaml = DeterministicYAML.to_deterministic_yaml(test_data)
    print("Deterministic YAML:")
    print(deterministic_yaml)
    print()
    
    # Parse with PyYAML
    parsed_pyyaml = yaml.safe_load(deterministic_yaml)
    print(f"Parsed by PyYAML: {parsed_pyyaml}")
    print(f"Matches original: {parsed_pyyaml == test_data}")
    assert parsed_pyyaml == test_data, "PyYAML parsed data doesn't match original"
    
    # Parse with custom parser
    parsed_custom = parse_deterministic_yaml(deterministic_yaml)
    print(f"Parsed by custom parser: {parsed_custom}")
    print(f"Matches original: {parsed_custom == test_data}")
    assert parsed_custom == test_data, "Custom parser parsed data doesn't match original"
    
    # Round-trip: parse and regenerate
    regenerated = DeterministicYAML.to_deterministic_yaml(parsed_pyyaml)
    print(f"\nRegenerated Deterministic YAML:")
    print(regenerated)
    print(f"Matches original YAML: {regenerated == deterministic_yaml}")
    assert regenerated == deterministic_yaml, "Regenerated YAML doesn't match original"


if __name__ == "__main__":
    test_yaml_compatibility()
    test_round_trip()

