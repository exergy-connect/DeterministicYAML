"""
Restricted YAML syntax definition and utilities.

This defines a subset of YAML that:
1. Reduces variance (more deterministic)
2. Maintains token efficiency (fewer tokens than JSON)
3. Is easier for LLMs to generate consistently
4. Fully deterministic (same data → same YAML)
"""

import yaml
import json
import re
from typing import Any, Dict, List, Optional, Union


class RestrictedYAML:
    """
    Restricted YAML syntax specification with strict deterministic rules.
    """
    
    # YAML indicator characters
    YAML_INDICATORS = set(': # | > - { } [ ] & * ! % @ `')
    YAML_START_INDICATORS = set('- ? : [ ] { } ! * & # | > \' " % @')
    
    # Patterns that must be quoted
    INTEGER_PATTERN = re.compile(r'^-?[0-9]+$')
    FLOAT_PATTERN = re.compile(r'^-?[0-9]+\.[0-9]+$')
    LEADING_ZERO_PATTERN = re.compile(r'^0[0-9]')
    TIMESTAMP_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}')
    
    @staticmethod
    def needs_quotes(value: str) -> bool:
        """
        Determine if a string value needs quotes (deterministic rules).
        
        Rule: Quote if ANY of the following apply:
        1. Contains any YAML indicator
        2. Starts with any indicator character
        3. Starts or ends with whitespace
        4. Is empty
        5. Matches YAML scalar patterns (integers, floats, booleans, null, etc.)
        6. Contains a newline
        7. Contains numeric-looking patterns (leading zeros, underscores, etc.)
        """
        if not value:
            return True  # Empty string must be quoted
        
        # Check for YAML indicators
        if any(char in RestrictedYAML.YAML_INDICATORS for char in value):
            return True
        
        # Check if starts with indicator character
        if value[0] in RestrictedYAML.YAML_START_INDICATORS:
            return True
        
        # Check if starts or ends with whitespace
        if value[0].isspace() or value[-1].isspace():
            return True
        
        # Check if contains newline
        if '\n' in value or '\r' in value:
            return True
        
        # Check if matches integer pattern
        if RestrictedYAML.INTEGER_PATTERN.match(value):
            return True
        
        # Check if matches float pattern
        if RestrictedYAML.FLOAT_PATTERN.match(value):
            return True
        
        # Check for leading zeros (e.g., 01, 007)
        if RestrictedYAML.LEADING_ZERO_PATTERN.match(value):
            return True
        
        # Check for underscores in numeric context (e.g., 1_000)
        # But allow underscores in identifiers (e.g., hello_world)
        if '_' in value and RestrictedYAML.INTEGER_PATTERN.match(value.replace('_', '')):
            return True
        
        # Check for plus signs (e.g., +42, +.5)
        if value.startswith('+'):
            return True
        
        # Check for octal/hex notation
        if re.match(r'^0[oOxX]', value):
            return True
        
        # Check for timestamps
        if RestrictedYAML.TIMESTAMP_PATTERN.match(value):
            return True
        
        # Check for floats without leading digits (e.g., .5)
        if re.match(r'^\.\d', value):
            return True
        
        # Check for special YAML values
        special_values = {
            'true', 'false', 'null', 'yes', 'no', 'on', 'off',
            'Yes', 'No', 'ON', 'OFF', 'True', 'False', 'NULL',
            '.nan', '.inf', '+.inf', '-.inf', '~'
        }
        if value in special_values:
            return True
        
        # Check if it looks like a number with exponent
        if 'e' in value.lower() and re.match(r'^-?\d+\.?\d*[eE][+-]?\d+$', value):
            return True
        
        return False
    
    @staticmethod
    def escape_string(value: str) -> str:
        """
        Escape a string using minimal deterministic escape set.
        
        Escapes only:
        - backslash → double backslash
        - quote → escaped quote
        - newline → \\n
        - tab → \\t
        - control chars → \\xNN
        """
        result = []
        for char in value:
            if char == '\\':
                result.append('\\\\')
            elif char == '"':
                result.append('\\"')
            elif char == '\n':
                result.append('\\n')
            elif char == '\t':
                result.append('\\t')
            elif ord(char) < 32:  # Control characters
                hex_val = format(ord(char), '02x')
                result.append('\\x' + hex_val)
            else:
                result.append(char)
        return ''.join(result)
    
    @staticmethod
    def canonicalize_number(value: Union[int, float]) -> str:
        """
        Canonicalize a number to strict format.
        
        Integers: base-10, no leading zeros, no + sign, no underscores
        Floats: decimal, at least one digit before and after decimal point
        """
        if isinstance(value, int):
            return str(value)
        
        elif isinstance(value, float):
            # Check for special float values
            if value != value:  # NaN
                return '".nan"'  # Must be quoted
            if value == float('inf'):
                return '".inf"'  # Must be quoted
            if value == float('-inf'):
                return '"-.inf"'  # Must be quoted
            
            # Convert to string with at least one digit before and after decimal
            s = str(value)
            
            # Handle scientific notation (shouldn't happen, but be safe)
            if 'e' in s.lower():
                # Can't represent in canonical form, quote it
                return f'"{s}"'
            
            # Ensure at least one digit before decimal
            if s.startswith('.'):
                s = '0' + s
            
            # Ensure at least one digit after decimal
            if '.' in s and s.endswith('.'):
                s = s + '0'
            elif '.' not in s:
                s = s + '.0'
            
            # Remove trailing zeros after decimal (but keep at least one)
            if '.' in s:
                parts = s.split('.')
                if len(parts) == 2:
                    integer_part = parts[0]
                    decimal_part = parts[1].rstrip('0') or '0'
                    s = f'{integer_part}.{decimal_part}'
            
            return s
        
        return str(value)
    
    @staticmethod
    def to_restricted_yaml(data: Any, indent: int = 0) -> str:
        """
        Convert Python data structure to restricted YAML.
        
        Args:
            data: Python object (dict, list, str, int, float, bool, None)
            indent: Current indentation level
        
        Returns:
            Restricted YAML string
        """
        indent_str = '  ' * indent
        
        if data is None:
            return 'null'
        
        elif isinstance(data, bool):
            return 'true' if data else 'false'
        
        elif isinstance(data, int):
            return RestrictedYAML.canonicalize_number(data)
        
        elif isinstance(data, float):
            return RestrictedYAML.canonicalize_number(data)
        
        elif isinstance(data, str):
            if RestrictedYAML.needs_quotes(data):
                escaped = RestrictedYAML.escape_string(data)
                return f'"{escaped}"'
            else:
                return data
        
        elif isinstance(data, list):
            if not data:
                return '[]'  # Canonical empty list
            
            lines = []
            for item in data:
                item_yaml = RestrictedYAML.to_restricted_yaml(item, indent + 1)
                # List items are indented one level more
                lines.append(f'{indent_str}- {item_yaml}')
            
            return '\n'.join(lines)
        
        elif isinstance(data, dict):
            if not data:
                return '{}'  # Canonical empty mapping
            
            lines = []
            # Sort keys lexicographically (Unicode codepoint ordering)
            for key, value in sorted(data.items()):
                # Key: always unquoted (must be IDENT pattern)
                key_str = str(key)
                if not re.match(r'^[A-Za-z0-9_]+$', key_str):
                    # Invalid key - should quote or reject
                    # For now, quote it (but this violates spec)
                    key_str = f'"{RestrictedYAML.escape_string(key_str)}"'
                
                # Value
                value_yaml = RestrictedYAML.to_restricted_yaml(value, indent + 1)
                
                # If value is multiline (list or dict), put key: on one line, value on next
                if isinstance(value, (dict, list)) and value:
                    lines.append(f'{indent_str}{key_str}:')
                    # Value is already indented, but we need to add one more level for nested content
                    value_lines = value_yaml.split('\n')
                    for line in value_lines:
                        lines.append(line)
                else:
                    lines.append(f'{indent_str}{key_str}: {value_yaml}')
            
            return '\n'.join(lines)
        
        else:
            # Fallback: convert to string and quote
            return f'"{RestrictedYAML.escape_string(str(data))}"'
    
    @staticmethod
    def validate(yaml_str: str) -> tuple[bool, Optional[str]]:
        """
        Validate that YAML string conforms to restricted syntax.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Parse to check if valid YAML
            data = yaml.safe_load(yaml_str)
            
            # Check for violations
            violations = []
            
            # Check for comments
            if '#' in yaml_str:
                lines = yaml_str.split('\n')
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        violations.append(f"Line {i}: Comments not allowed")
            
            # Check for document markers
            if yaml_str.strip().startswith('---') or '...' in yaml_str:
                violations.append("Document markers (---, ...) not allowed")
            
            # Check for anchors/aliases
            if '&' in yaml_str or '*' in yaml_str:
                violations.append("Anchors (&) and aliases (*) not allowed")
            
            # Check for tabs
            if '\t' in yaml_str:
                violations.append("Tabs not allowed, use 2 spaces for indentation")
            
            # Check for trailing spaces
            for i, line in enumerate(yaml_str.split('\n'), 1):
                if line.rstrip() != line and line.strip():
                    violations.append(f"Line {i}: Trailing spaces not allowed")
            
            # Check for blank lines inside structures (simplified check)
            # This is approximate - full check would need proper parsing
            
            if violations:
                return False, '; '.join(violations)
            
            return True, None
            
        except yaml.YAMLError as e:
            return False, f"Invalid YAML: {str(e)}"
    
    @staticmethod
    def normalize(yaml_str: str) -> str:
        """
        Normalize YAML to restricted format.
        
        This converts any valid YAML to restricted YAML format.
        """
        try:
            data = yaml.safe_load(yaml_str)
            return RestrictedYAML.to_restricted_yaml(data)
        except Exception as e:
            raise ValueError(f"Failed to normalize YAML: {e}")


def compare_formats():
    """Compare JSON, standard YAML, and restricted YAML."""
    test_data = {
        'name': 'John',
        'age': 30,
        'active': True,
        'tags': ['important', 'urgent'],
        'config': {
            'host': 'localhost',
            'port': 5432
        }
    }
    
    # Generate different formats
    json_str = json.dumps(test_data, indent=2)
    json_compact = json.dumps(test_data)
    yaml_standard = yaml.dump(test_data, default_flow_style=False)
    yaml_restricted = RestrictedYAML.to_restricted_yaml(test_data)
    
    print("=" * 80)
    print("FORMAT COMPARISON")
    print("=" * 80)
    
    print("\nJSON (pretty):")
    print(json_str)
    
    print("\nJSON (compact):")
    print(json_compact)
    
    print("\nYAML (standard):")
    print(yaml_standard)
    
    print("\nYAML (restricted):")
    print(yaml_restricted)
    
    # Count tokens (approximation)
    def count_tokens(text):
        return len(text) // 4
    
    json_tokens = count_tokens(json_str)
    json_compact_tokens = count_tokens(json_compact)
    yaml_standard_tokens = count_tokens(yaml_standard)
    yaml_restricted_tokens = count_tokens(yaml_restricted)
    
    print("\n" + "=" * 80)
    print("TOKEN COUNT COMPARISON")
    print("=" * 80)
    print(f"JSON (pretty):        {json_tokens:3d} tokens")
    print(f"JSON (compact):       {json_compact_tokens:3d} tokens")
    print(f"YAML (standard):      {yaml_standard_tokens:3d} tokens")
    print(f"YAML (restricted):    {yaml_restricted_tokens:3d} tokens")
    
    print("\n" + "=" * 80)
    print("DETERMINISTIC QUOTING TEST")
    print("=" * 80)
    
    # Test deterministic quoting
    test_strings = [
        ('John', False),  # Should not be quoted
        ('John Doe', True),  # Contains space, should be quoted
        ('', True),  # Empty, should be quoted
        ('42', True),  # Looks like number, should be quoted
        ('true', True),  # Looks like boolean, should be quoted
        ('hello_world', False),  # Should not be quoted
        ('hello-world', True),  # Contains -, should be quoted
        ('hello:world', True),  # Contains :, should be quoted
    ]
    
    print("\nString quoting rules:")
    for value, should_quote in test_strings:
        needs_quotes = RestrictedYAML.needs_quotes(value)
        status = "✓" if needs_quotes == should_quote else "✗"
        quoted = f'"{value}"' if needs_quotes else value
        print(f"  {status} {repr(value):20s} → {quoted}")


if __name__ == "__main__":
    compare_formats()
