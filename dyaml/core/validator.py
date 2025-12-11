"""
Deterministic YAML validation.

This module validates YAML files against the Deterministic YAML specification.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml
import re

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'lib'))

try:
    from deterministic_yaml import DeterministicYAML
except ImportError:
    DeterministicYAML = None


class ValidationError:
    """Represents a validation error."""
    
    def __init__(self, line: int, message: str, severity: str = "error"):
        self.line = line
        self.message = message
        self.severity = severity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "line": self.line,
            "message": self.message,
            "severity": self.severity
        }


class ValidationResult:
    """Result of validation with errors and warnings."""
    
    def __init__(self, valid: bool, errors: List[ValidationError], warnings: List[ValidationError]):
        self.valid = valid
        self.errors = errors
        self.warnings = warnings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings]
        }


def validate_file(file_path: str, strict: bool = False) -> ValidationResult:
    """
    Validate a Deterministic YAML file.
    
    Args:
        file_path: Path to YAML file
        strict: If True, perform stricter validation
        
    Returns:
        ValidationResult object
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return validate_string(content, strict)


def validate_string(yaml_str: str, strict: bool = False) -> ValidationResult:
    """
    Validate a Deterministic YAML string.
    
    Args:
        yaml_str: YAML string content
        strict: If True, perform stricter validation
        
    Returns:
        ValidationResult object
    """
    errors = []
    warnings = []
    
    # Check if valid YAML first
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        errors.append(ValidationError(0, f"Invalid YAML: {str(e)}"))
        return ValidationResult(False, errors, warnings)
    
    lines = yaml_str.split('\n')
    
    # Check for comments (not allowed in D-YAML)
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        
        # Line comments
        if stripped.startswith('#'):
            errors.append(ValidationError(i, "Comments not allowed (use $human$ fields instead)"))
            continue
        
        # Inline comments
        if '#' in line:
            # Check if # is inside quotes
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
                after_hash = line[hash_pos + 1:].strip()
                if after_hash:
                    errors.append(ValidationError(i, "Inline comments not allowed (use $human$ fields instead)"))
    
    # Check for document markers
    if yaml_str.strip().startswith('---') or '...' in yaml_str:
        errors.append(ValidationError(0, "Document markers (---, ...) not allowed"))
    
    # Check for anchors/aliases
    if '&' in yaml_str or '*' in yaml_str:
        errors.append(ValidationError(0, "Anchors (&) and aliases (*) not allowed"))
    
    # Check for tabs
    for i, line in enumerate(lines, start=1):
        if '\t' in line:
            errors.append(ValidationError(i, "Tabs not allowed, use 2 spaces for indentation"))
    
    # Check for trailing spaces
    for i, line in enumerate(lines, start=1):
        if line.rstrip() != line and line.strip():
            errors.append(ValidationError(i, "Trailing spaces not allowed"))
    
    # Check for flow style
    if '{' in yaml_str or '[' in yaml_str:
        # Check if it's inside quotes
        if not _is_inside_quotes(yaml_str, yaml_str.find('{')):
            errors.append(ValidationError(0, "Flow style ({}, []) not allowed, use block style"))
    
    # Validate data structure
    if data is not None:
        struct_errors, struct_warnings = _validate_structure(data, yaml_str)
        errors.extend(struct_errors)
        warnings.extend(struct_warnings)
    
    # Check key ordering (if DeterministicYAML available)
    if DeterministicYAML:
        is_valid, error_msg = DeterministicYAML.validate(yaml_str)
        if not is_valid:
            # Parse error message to extract line numbers if possible
            errors.append(ValidationError(0, error_msg))
    
    valid = len(errors) == 0
    return ValidationResult(valid, errors, warnings)


def _validate_structure(data: Any, yaml_str: str, path: List[str] = None) -> Tuple[List[ValidationError], List[ValidationError]]:
    """Validate data structure against D-YAML rules."""
    errors = []
    warnings = []
    
    if path is None:
        path = []
    
    if isinstance(data, dict):
        # Check for multiple $human$ fields
        human_count = sum(1 for k in data.keys() if k == '$human$')
        if human_count > 1:
            errors.append(ValidationError(0, f"Multiple $human$ fields in object at path {'.'.join(path)} (only one allowed)"))
        
        # Check if $human$ is first
        keys_list = list(data.keys())
        if '$human$' in keys_list:
            human_index = keys_list.index('$human$')
            if human_index != 0:
                warnings.append(ValidationError(0, f"$human$ field should be first in object at path {'.'.join(path)}"))
        
        # Check key ordering (should be sorted lexicographically with $human$ first)
        sorted_keys = sorted([k for k in keys_list if k != '$human$'])
        expected_order = (['$human$'] if '$human$' in keys_list else []) + sorted_keys
        
        if keys_list != expected_order:
            warnings.append(ValidationError(0, f"Keys not in lexicographic order in object at path {'.'.join(path)}"))
        
        # Validate nested structures
        for key, value in data.items():
            nested_path = path + [str(key)]
            nested_errors, nested_warnings = _validate_structure(value, yaml_str, nested_path)
            errors.extend(nested_errors)
            warnings.extend(nested_warnings)
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            nested_path = path + [str(i)]
            nested_errors, nested_warnings = _validate_structure(item, yaml_str, nested_path)
            errors.extend(nested_errors)
            warnings.extend(nested_warnings)
    
    return errors, warnings


def _is_inside_quotes(text: str, pos: int) -> bool:
    """Check if a position in text is inside quoted string."""
    before = text[:pos]
    quote_count = before.count('"') + before.count("'")
    # Simple heuristic: if odd number of quotes before, we're inside
    return quote_count % 2 == 1

