"""
Parser for Restricted YAML based on the formal grammar.

Grammar:
  yaml ::= element(0)
  element(indent) ::= mapping(indent) | list(indent) | scalar
  mapping(indent) ::= pair(indent) | pair(indent) mapping(indent)
  pair(indent) ::= INDENT(indent) key ":" SP value(indent + 1)
  list(indent) ::= list_item(indent) | list_item(indent) list(indent)
  list_item(indent) ::= INDENT(indent) "-" SP list_value(indent + 1)
  scalar ::= IDENT | QUOTED | NUMBER | BOOLEAN | NULL

Copyright (c) 2025 Exergy LLC

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

import re
from typing import Any, List, Tuple, Optional, Union


class RestrictedYAMLParser:
    """Parser for Restricted YAML based on formal grammar."""
    
    # Token patterns
    IDENT_PATTERN = re.compile(r'^[A-Za-z0-9_]+$')
    NUMBER_PATTERN = re.compile(r'^-?[0-9]+$')
    QUOTED_PATTERN = re.compile(r'^"(?:[^"\\]|\\.)*"$')
    BOOLEAN_VALUES = {'true', 'false'}
    NULL_VALUE = 'null'
    
    def __init__(self, text: str):
        """Initialize parser with YAML text."""
        self.text = text
        self.lines = [line for line in text.split('\n') if line.strip() or line == '']
        self.pos = 0
    
    def parse(self) -> Any:
        """Parse the YAML text and return Python object."""
        if not self.lines:
            return None
        
        # Remove empty lines at start
        while self.pos < len(self.lines) and not self.lines[self.pos].strip():
            self.pos += 1
        
        if self.pos >= len(self.lines):
            return None
        
        # Parse element at indent level 0
        return self.parse_element(0)
    
    def parse_element(self, indent: int) -> Any:
        """Parse an element at given indent level."""
        if self.pos >= len(self.lines):
            return None
        
        line = self.lines[self.pos]
        stripped = line.lstrip()
        current_indent_spaces = len(line) - len(stripped)
        current_indent_level = current_indent_spaces // 2
        
        # Must be at correct indent level
        if current_indent_level != indent:
            return None
        
        # Check if this is a mapping (starts with IDENT:)
        if re.match(r'^[A-Za-z0-9_]+:\s*', stripped):
            return self.parse_mapping(indent)
        
        # Check if this is a list (starts with -)
        if stripped.startswith('- '):
            return self.parse_list(indent)
        
        # Otherwise, it's a scalar
        return self.parse_scalar()
    
    def parse_mapping(self, indent: int) -> dict:
        """Parse a mapping (key-value pairs) at given indent level."""
        result = {}
        
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            stripped = line.lstrip()
            current_indent_spaces = len(line) - len(stripped)
            current_indent_level = current_indent_spaces // 2
            
            # Stop if indent decreases
            if current_indent_level < indent:
                break
            
            # Skip if not at correct indent
            if current_indent_level != indent:
                self.pos += 1
                continue
            
            # Parse pair
            pair = self.parse_pair(indent)
            if pair:
                key, value = pair
                result[key] = value
            else:
                break
        
        return result
    
    def parse_pair(self, indent: int) -> Optional[Tuple[str, Any]]:
        """Parse a key-value pair at given indent level."""
        if self.pos >= len(self.lines):
            return None
        
        line = self.lines[self.pos]
        stripped = line.lstrip()
        current_indent_spaces = len(line) - len(stripped)
        current_indent_level = current_indent_spaces // 2
        
        if current_indent_level != indent:
            return None
        
        # Parse key: value or key:
        match = re.match(r'^([A-Za-z0-9_]+):\s*(.*)$', stripped)
        if not match:
            return None
        
        key = match.group(1)
        value_str = match.group(2).strip()
        
        self.pos += 1
        
        # If value is on same line and is a scalar
        if value_str and self.is_scalar(value_str):
            value = self.parse_scalar_string(value_str)
            return (key, value)
        
        # Value is on next line(s) at indent + 1, or empty
        # Check if next line exists and has correct indent
        if self.pos < len(self.lines):
            # Skip empty lines
            saved_pos = self.pos
            while self.pos < len(self.lines):
                line = self.lines[self.pos]
                if line.strip():
                    break
                self.pos += 1
            
            if self.pos < len(self.lines):
                next_line = self.lines[self.pos]
                next_stripped = next_line.lstrip()
                next_indent = len(next_line) - len(next_stripped)
                
                # Convert spaces to indent level (2 spaces per level)
                next_indent_level = next_indent // 2
                if next_indent_level == indent + 1:
                    # Value is a mapping or list at indent + 1
                    value = self.parse_element(indent + 1)
                    return (key, value)
                elif next_indent_level <= indent:
                    # No value, or empty value
                    self.pos = saved_pos  # Restore position
                    return (key, None)
            else:
                # No more lines
                self.pos = saved_pos
                return (key, None)
        
        # No more lines
        return (key, None)
    
    def parse_value(self, indent: int) -> Any:
        """Parse a value at given indent level."""
        # Skip empty lines
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            stripped = line.lstrip()
            if not stripped:
                self.pos += 1
                continue
            break
        
        if self.pos >= len(self.lines):
            return None
        
        line = self.lines[self.pos]
        stripped = line.lstrip()
        current_indent_spaces = len(line) - len(stripped)
        current_indent_level = current_indent_spaces // 2
        
        # If current line is at correct indent, parse as element
        if current_indent_level == indent:
            return self.parse_element(indent)
        
        # If indent is less, return None (value not found)
        if current_indent_level < indent:
            return None
        
        # Indent is greater, which shouldn't happen for a value
        # But skip and try next line
        self.pos += 1
        return self.parse_value(indent)
    
    def parse_list(self, indent: int) -> list:
        """Parse a list at given indent level."""
        result = []
        
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            stripped = line.lstrip()
            current_indent_spaces = len(line) - len(stripped)
            current_indent_level = current_indent_spaces // 2
            
            # Stop if indent decreases
            if current_indent_level < indent:
                break
            
            # Skip if not at correct indent
            if current_indent_level != indent:
                self.pos += 1
                continue
            
            # Parse list item
            if stripped.startswith('- '):
                value_str = stripped[2:].lstrip()
                self.pos += 1
                
                # If value is on same line and is a scalar
                if value_str and self.is_scalar(value_str):
                    value = self.parse_scalar_string(value_str)
                    result.append(value)
                else:
                    # Value is on next line(s) at indent + 1, or empty
                    if self.pos < len(self.lines):
                        next_line = self.lines[self.pos]
                        next_stripped = next_line.lstrip()
                        next_indent = len(next_line) - len(next_stripped)
                        
                        # Convert spaces to indent level (2 spaces per level)
                        next_indent_level = next_indent // 2
                        if next_indent_level == indent + 1:
                            # Value is a mapping or list
                            value = self.parse_element(indent + 1)
                            result.append(value)
                        else:
                            # Empty value or scalar on same line
                            if value_str:
                                value = self.parse_scalar_string(value_str)
                                result.append(value)
                            else:
                                result.append(None)
                    else:
                        # No more lines, empty value
                        if value_str:
                            value = self.parse_scalar_string(value_str)
                            result.append(value)
                        else:
                            result.append(None)
            else:
                break
        
        return result
    
    def parse_scalar(self) -> Any:
        """Parse a scalar value."""
        if self.pos >= len(self.lines):
            return None
        
        line = self.lines[self.pos]
        stripped = line.lstrip()
        self.pos += 1
        
        return self.parse_scalar_string(stripped)
    
    def parse_scalar_string(self, s: str) -> Any:
        """Parse a scalar string into Python value."""
        s = s.strip()
        
        if not s:
            return None
        
        # NULL
        if s == 'null':
            return None
        
        # BOOLEAN
        if s in self.BOOLEAN_VALUES:
            return s == 'true'
        
        # NUMBER
        if self.NUMBER_PATTERN.match(s):
            return int(s)
        
        # QUOTED
        if s.startswith('"') and s.endswith('"'):
            return self.parse_quoted_string(s)
        
        # IDENT (unquoted identifier)
        if self.IDENT_PATTERN.match(s):
            return s
        
        # If it doesn't match any pattern, treat as string (shouldn't happen in valid YAML)
        return s
    
    def parse_quoted_string(self, s: str) -> str:
        """Parse a quoted string with escape sequences."""
        # Remove quotes
        content = s[1:-1]
        
        # Handle escape sequences
        result = []
        i = 0
        while i < len(content):
            if content[i] == '\\' and i + 1 < len(content):
                next_char = content[i + 1]
                if next_char == 'n':
                    result.append('\n')
                    i += 2
                elif next_char == 't':
                    result.append('\t')
                    i += 2
                elif next_char == 'r':
                    result.append('\r')
                    i += 2
                elif next_char == '\\':
                    result.append('\\')
                    i += 2
                elif next_char == '"':
                    result.append('"')
                    i += 2
                else:
                    result.append(content[i])
                    i += 1
            else:
                result.append(content[i])
                i += 1
        
        return ''.join(result)
    
    def is_scalar(self, s: str) -> bool:
        """Check if string is a scalar (not a mapping or list)."""
        s = s.strip()
        
        # Empty is not a scalar (will be handled separately)
        if not s:
            return False
        
        # Quoted strings are scalars
        if s.startswith('"') and s.endswith('"'):
            return True
        
        # Check if it looks like a mapping start (key:)
        if re.match(r'^[A-Za-z0-9_]+:\s*$', s):
            return False
        
        # Check if it looks like a list start (-)
        if s.startswith('- '):
            return False
        
        # Otherwise it's a scalar (IDENT, NUMBER, BOOLEAN, NULL, or quoted)
        return True


def parse_restricted_yaml(text: str) -> Any:
    """Parse Restricted YAML text into Python object."""
    parser = RestrictedYAMLParser(text)
    return parser.parse()


def test_parser():
    """Test the parser with various examples."""
    print("=" * 80)
    print("RESTRICTED YAML PARSER TESTS")
    print("=" * 80)
    
    test_cases = [
        ("name: John\nage: 30", {"name": "John", "age": 30}),
        ("- item1\n- item2", ["item1", "item2"]),
        ("active: true\ncount: 42", {"active": True, "count": 42}),
        ("value: null", {"value": None}),
        ('description: "Hello\\nWorld"', {"description": "Hello\nWorld"}),
        ("config:\n  host: localhost\n  port: 5432", 
         {"config": {"host": "localhost", "port": 5432}}),
        ("tags:\n  - dev\n  - ops", {"tags": ["dev", "ops"]}),
    ]
    
    for i, (yaml_text, expected) in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"  Input: {repr(yaml_text)}")
        try:
            result = parse_restricted_yaml(yaml_text)
            print(f"  Result: {result}")
            print(f"  Expected: {expected}")
            if result == expected:
                print(f"  ✓ PASS")
            else:
                print(f"  ✗ FAIL")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")


if __name__ == "__main__":
    test_parser()

