"""
Deterministic YAML syntax definition and utilities.

This defines a subset of YAML that:
1. Reduces variance (more deterministic)
2. Maintains token efficiency (fewer tokens than JSON)
3. Is easier for LLMs to generate consistently
4. Fully deterministic (same data → same YAML)

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
import json
import re
from typing import Any, Dict, List, Optional, Union


class DeterministicYAML:
    """
    Deterministic YAML syntax specification with strict deterministic rules.
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
        if any(char in DeterministicYAML.YAML_INDICATORS for char in value):
            return True
        
        # Check if starts with indicator character
        if value[0] in DeterministicYAML.YAML_START_INDICATORS:
            return True
        
        # Check if starts or ends with whitespace
        if value[0].isspace() or value[-1].isspace():
            return True
        
        # Check if contains newline
        if '\n' in value or '\r' in value:
            return True
        
        # Check if matches integer pattern
        if DeterministicYAML.INTEGER_PATTERN.match(value):
            return True
        
        # Check if matches float pattern
        if DeterministicYAML.FLOAT_PATTERN.match(value):
            return True
        
        # Check for leading zeros (e.g., 01, 007)
        if DeterministicYAML.LEADING_ZERO_PATTERN.match(value):
            return True
        
        # Check for underscores in numeric context (e.g., 1_000)
        # But allow underscores in identifiers (e.g., hello_world)
        if '_' in value and DeterministicYAML.INTEGER_PATTERN.match(value.replace('_', '')):
            return True
        
        # Check for plus signs (e.g., +42, +.5)
        if value.startswith('+'):
            return True
        
        # Check for octal/hex notation
        if re.match(r'^0[oOxX]', value):
            return True
        
        # Check for timestamps
        if DeterministicYAML.TIMESTAMP_PATTERN.match(value):
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
    def to_deterministic_yaml(data: Any, indent: int = 0) -> str:
        """
        Convert Python data structure to deterministic YAML.
        
        Args:
            data: Python object (dict, list, str, int, float, bool, None)
            indent: Current indentation level
        
        Returns:
            Deterministic YAML string
        """
        indent_str = '  ' * indent
        
        if data is None:
            return 'null'
        
        elif isinstance(data, bool):
            return 'true' if data else 'false'
        
        elif isinstance(data, int):
            return DeterministicYAML.canonicalize_number(data)
        
        elif isinstance(data, float):
            return DeterministicYAML.canonicalize_number(data)
        
        elif isinstance(data, str):
            if DeterministicYAML.needs_quotes(data):
                escaped = DeterministicYAML.escape_string(data)
                return f'"{escaped}"'
            else:
                return data
        
        elif isinstance(data, list):
            if not data:
                return '[]'  # Canonical empty list
            
            lines = []
            for item in data:
                item_yaml = DeterministicYAML.to_deterministic_yaml(item, indent + 1)
                # List items are indented one level more
                lines.append(f'{indent_str}- {item_yaml}')
            
            return '\n'.join(lines)
        
        elif isinstance(data, dict):
            if not data:
                return '{}'  # Canonical empty mapping
            
            lines = []
            # Sort keys: $human$ first, then lexicographically (Unicode codepoint ordering)
            sorted_items = sorted(data.items())
            # Move $human$ to the front if it exists
            human_key = '$human$'
            sorted_items = [(k, v) for k, v in sorted_items if k == human_key] + \
                          [(k, v) for k, v in sorted_items if k != human_key]
            
            for key, value in sorted_items:
                # Key: always unquoted (must be IDENT pattern, or $human$)
                key_str = str(key)
                if key_str == '$human$':
                    # $human$ is a special reserved key
                    key_str = '$human$'
                elif not re.match(r'^[A-Za-z0-9_]+$', key_str):
                    # Invalid key - should quote or reject
                    # For now, quote it (but this violates spec)
                    key_str = f'"{DeterministicYAML.escape_string(key_str)}"'
                
                # Value
                value_yaml = DeterministicYAML.to_deterministic_yaml(value, indent + 1)
                
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
            return f'"{DeterministicYAML.escape_string(str(data))}"'
    
    @staticmethod
    def validate(yaml_str: str) -> tuple[bool, Optional[str]]:
        """
        Validate that YAML string conforms to deterministic syntax.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Parse to check if valid YAML
            data = yaml.safe_load(yaml_str)
            
            # Check for violations
            violations = []
            
            # Check for comments (both line and inline)
            if '#' in yaml_str:
                lines = yaml_str.split('\n')
                in_quoted_string = False
                quote_char = None
                
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    
                    # Check if line starts with comment (line comment)
                    if stripped.startswith('#'):
                        violations.append(f"Line {i}: Comments not allowed")
                        continue
                    
                    # Check for inline comments (simplified - doesn't handle all edge cases)
                    # Look for # that's not inside a quoted string
                    if '#' in line:
                        # Simple heuristic: if # appears and line doesn't end with quote,
                        # and # is not immediately after a quote, it's likely a comment
                        # This is approximate - full parsing would be more accurate
                        parts = line.split('#')
                        if len(parts) > 1:
                            # Check if # is in a quoted string by counting quotes
                            before_hash = parts[0]
                            quote_count_before = before_hash.count('"') + before_hash.count("'")
                            # If even number of quotes before #, we're outside a string
                            if quote_count_before % 2 == 0:
                                # Check if there's content after # (not just whitespace/end)
                                after_hash = '#'.join(parts[1:])
                                if after_hash.strip() and not after_hash.strip().startswith('"'):
                                    violations.append(f"Line {i}: Inline comments not allowed")
            
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
    def _extract_comments(yaml_str: str) -> List[Dict[str, Any]]:
        """
        Extract comments from YAML text with their context.
        
        Returns a list of comment dictionaries with:
        - line_index: line number (0-based)
        - indent_level: indentation level
        - comment_text: the comment text
        - type: 'line' or 'inline'
        - key_context: the key this comment is associated with (if determinable)
        """
        comments = []
        lines = yaml_str.split('\n')
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Calculate indentation level (2 spaces per level)
            indent_spaces = len(line) - len(line.lstrip())
            indent_level = indent_spaces // 2
            
            # Check for line comments (entire line is a comment)
            if stripped.startswith('#'):
                comment_text = stripped[1:].strip()
                if comment_text:
                    comments.append({
                        'line_index': i,
                        'indent_level': indent_level,
                        'comment_text': comment_text,
                        'type': 'line',
                        'key_context': None
                    })
                continue
            
            # Check for inline comments
            if '#' in line:
                # Check if # is inside a quoted string
                in_quotes = False
                quote_char = None
                hash_pos = -1
                
                for j, char in enumerate(line):
                    if char in ('"', "'") and (j == 0 or line[j-1] != '\\'):
                        if not in_quotes:
                            in_quotes = True
                            quote_char = char
                        elif char == quote_char:
                            in_quotes = False
                            quote_char = None
                    elif char == '#' and not in_quotes:
                        hash_pos = j
                        break
                
                if hash_pos >= 0:
                    before_hash = line[:hash_pos].rstrip()
                    after_hash = line[hash_pos + 1:].strip()
                    if after_hash:
                        # Try to extract the key this comment is associated with
                        key_context = None
                        if ':' in before_hash:
                            # Extract key from "key: value" pattern
                            key_match = re.match(r'^(\s*)([A-Za-z0-9_]+)\s*:', before_hash)
                            if key_match:
                                key_context = key_match.group(2)
                        
                        comments.append({
                            'line_index': i,
                            'indent_level': indent_level,
                            'comment_text': after_hash,
                            'type': 'inline',
                            'key_context': key_context
                        })
        
        return comments
    
    @staticmethod
    def _add_comments_to_structure(data: Any, comments: List[Dict[str, Any]], path: Optional[List[str]] = None) -> Any:
        """
        Recursively add extracted comments to the data structure as $human$ fields.
        
        This preserves human comments by converting them to $human$ key-value pairs.
        Comments are associated with their nearest key based on indentation and context.
        Only one $human$ field per object is allowed.
        """
        if path is None:
            path = []
        
        if isinstance(data, dict):
            result = {}
            
            # Preserve existing $human$ field (but only one)
            if '$human$' in data:
                human_value = data['$human$']
                # Strip empty $human$ values
                if human_value and str(human_value).strip():
                    result['$human$'] = human_value
            
            # Collect comments that belong to this level
            current_indent = len(path)
            level_comments = []
            
            for comment in comments:
                # Match comments to this level based on indent and path
                if comment['indent_level'] == current_indent:
                    # If comment has key_context, check if it matches a key at this level
                    if comment['key_context'] and comment['key_context'] in data:
                        # This comment belongs to a specific key
                        # We'll add it when processing that key
                        pass
                    else:
                        # This is a general comment for this level
                        level_comments.append(comment['comment_text'])
            
            # Add collected comments as $human$ field if we have any
            if level_comments:
                combined_comment = ' '.join(level_comments)
                if '$human$' in result:
                    # Combine with existing $human$ value
                    existing = str(result['$human$'])
                    result['$human$'] = f"{existing} {combined_comment}".strip()
                else:
                    result['$human$'] = combined_comment
            
            # Process each key-value pair (skip $human$ as we already handled it)
            for key, value in data.items():
                if key == '$human$':
                    continue
                
                # Check if there's a comment specifically for this key
                key_comments = []
                for comment in comments:
                    if (comment['key_context'] == key and 
                        comment['indent_level'] == current_indent):
                        # Include field name in the comment: "fieldname: comment text"
                        formatted_comment = f"{key}: {comment['comment_text']}"
                        key_comments.append(formatted_comment)
                
                # Recursively process the value
                new_path = path + [key]
                processed_value = DeterministicYAML._add_comments_to_structure(value, comments, new_path)
                
                # If this key has comments, add them to a nested $human$ if value is a dict
                if key_comments and isinstance(processed_value, dict):
                    key_comment = ' '.join(key_comments)
                    if '$human$' in processed_value:
                        # Combine with existing $human$ value
                        existing = str(processed_value['$human$'])
                        processed_value['$human$'] = f"{existing} {key_comment}".strip()
                    else:
                        processed_value['$human$'] = key_comment
                elif key_comments:
                    # If value is not a dict, add comment to parent level $human$
                    key_comment = ' '.join(key_comments)
                    if '$human$' in result:
                        existing = str(result['$human$'])
                        result['$human$'] = f"{existing} {key_comment}".strip()
                    else:
                        result['$human$'] = key_comment
                
                result[key] = processed_value
            
            return result
        elif isinstance(data, list):
            return [DeterministicYAML._add_comments_to_structure(item, comments, path) for item in data]
        else:
            return data
    
    @staticmethod
    def normalize(yaml_str: str, preserve_comments: bool = True) -> str:
        """
        Normalize YAML to deterministic format, optionally preserving human comments.
        
        This converts any valid YAML to deterministic YAML format.
        When preserve_comments=True, comments (both line and inline) are extracted 
        and converted to $human$ fields to preserve human insight as first-class data 
        that survives all operations.
        
        The normalize method:
        1. Extracts all comments from the original YAML text (if preserve_comments=True)
        2. Parses the YAML data structure
        3. Maps comments to their appropriate locations in the structure (if preserve_comments=True)
        4. Adds them as $human$ key-value pairs (appearing first in each object)
        5. Generates deterministic YAML with comments preserved as data (or stripped if preserve_comments=False)
        
        Args:
            yaml_str: Input YAML string (may contain # comments)
            preserve_comments: If True, convert comments to $human$ fields. If False, strip all comments
                             and existing $human$ fields (canonical mode).
        
        Returns:
            Deterministic YAML string with comments preserved as $human$ fields (if preserve_comments=True)
            or pure data without any $human$ fields (if preserve_comments=False)
        
        Example (preserve_comments=True):
            Input:
                # User profile
                name: John  # User's name
                age: 30
            
            Output:
                $human$: "User profile name: User's name"
                age: 30
                name: John
        
        Example (preserve_comments=False):
            Input:
                # User profile
                name: John  # User's name
                age: 30
            
            Output:
                age: 30
                name: John
        """
        try:
            # Parse the YAML data (this will lose comments)
            data = yaml.safe_load(yaml_str)
            
            if data is None:
                return 'null'
            
            if preserve_comments:
                # First, extract comments from the original text
                comments = DeterministicYAML._extract_comments(yaml_str)
                
                # If we have comments, add them to the data structure as $human$ fields
                if comments:
                    # Ensure root is a dict to hold comments
                    if not isinstance(data, dict):
                        data = {'_value': data}
                    
                    # Add comments to the structure
                    data = DeterministicYAML._add_comments_to_structure(data, comments)
            else:
                # Strip all $human$ fields for canonical mode
                data = DeterministicYAML.strip_human(data)
            
            return DeterministicYAML.to_deterministic_yaml(data)
        except Exception as e:
            raise ValueError(f"Failed to normalize YAML: {e}")
    
    @staticmethod
    def strip_human(data: Any) -> Any:
        """
        Remove all $human$ fields from a data structure.
        
        This is useful for canonical mode where pure data is needed,
        or before schema validation that doesn't expect $human$ fields.
        
        Args:
            data: Python data structure (dict, list, or scalar)
        
        Returns:
            Data structure with all $human$ fields removed
        
        Example:
            Input:
                {
                    '$human$': 'User profile',
                    'name': 'John',
                    'age': 30,
                    'config': {
                        '$human$': 'Database settings',
                        'host': 'localhost'
                    }
                }
            
            Output:
                {
                    'name': 'John',
                    'age': 30,
                    'config': {
                        'host': 'localhost'
                    }
                }
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key != '$human$':
                    result[key] = DeterministicYAML.strip_human(value)
            return result
        elif isinstance(data, list):
            return [DeterministicYAML.strip_human(item) for item in data]
        else:
            return data


def compare_formats():
    """Compare JSON, standard YAML, and deterministic YAML."""
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
    yaml_deterministic = DeterministicYAML.to_deterministic_yaml(test_data)
    
    print("=" * 80)
    print("FORMAT COMPARISON")
    print("=" * 80)
    
    print("\nJSON (pretty):")
    print(json_str)
    
    print("\nJSON (compact):")
    print(json_compact)
    
    print("\nYAML (standard):")
    print(yaml_standard)
    
    print("\nYAML (deterministic):")
    print(yaml_deterministic)
    
    # Count tokens (approximation)
    def count_tokens(text):
        return len(text) // 4
    
    json_tokens = count_tokens(json_str)
    json_compact_tokens = count_tokens(json_compact)
    yaml_standard_tokens = count_tokens(yaml_standard)
    yaml_deterministic_tokens = count_tokens(yaml_deterministic)
    
    print("\n" + "=" * 80)
    print("TOKEN COUNT COMPARISON")
    print("=" * 80)
    print(f"JSON (pretty):        {json_tokens:3d} tokens")
    print(f"JSON (compact):       {json_compact_tokens:3d} tokens")
    print(f"YAML (standard):      {yaml_standard_tokens:3d} tokens")
    print(f"YAML (deterministic):    {yaml_deterministic_tokens:3d} tokens")
    
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
        needs_quotes = DeterministicYAML.needs_quotes(value)
        status = "✓" if needs_quotes == should_quote else "✗"
        quoted = f'"{value}"' if needs_quotes else value
        print(f"  {status} {repr(value):20s} → {quoted}")


if __name__ == "__main__":
    compare_formats()
