"""
YAML parser with comment preservation using ruamel.yaml.

This module provides comment-aware parsing that extracts both
the data structure and comment information for conversion to $human$ fields.
"""

from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import sys

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
    RUAMEL_AVAILABLE = True
except ImportError:
    RUAMEL_AVAILABLE = False
    # Fallback to basic yaml if ruamel not available
    import yaml


class CommentInfo:
    """Information about a comment in the YAML structure."""
    
    def __init__(
        self,
        text: str,
        comment_type: str,  # 'line', 'inline', 'eol'
        line_number: int,
        key_path: Optional[List[str]] = None,
        associated_key: Optional[str] = None
    ):
        self.text = text
        self.comment_type = comment_type
        self.line_number = line_number
        self.key_path = key_path or []
        self.associated_key = associated_key
    
    def __repr__(self):
        return f"CommentInfo(text={self.text!r}, type={self.comment_type}, path={self.key_path})"


def parse_yaml_with_comments(file_path: str) -> Tuple[Any, List[CommentInfo]]:
    """
    Parse YAML file preserving comment structure.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Tuple of (data, comments) where:
        - data: Parsed YAML data structure
        - comments: List of CommentInfo objects
    """
    if not RUAMEL_AVAILABLE:
        # Fallback: use basic yaml parsing (loses comments)
        import yaml
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            data = yaml.safe_load(content)
            # Extract comments manually from text
            comments = _extract_comments_from_text(content)
            return data, comments
    
    yaml_parser = YAML()
    yaml_parser.preserve_quotes = True
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml_parser.load(f)
    
    # Extract comments from the parsed structure
    comments = _extract_comments_from_ruamel(data, yaml_parser)
    
    return data, comments


def parse_yaml_string_with_comments(yaml_str: str) -> Tuple[Any, List[CommentInfo]]:
    """
    Parse YAML string preserving comment structure.
    
    Args:
        yaml_str: YAML string content
        
    Returns:
        Tuple of (data, comments) where:
        - data: Parsed YAML data structure
        - comments: List of CommentInfo objects
    """
    if not RUAMEL_AVAILABLE:
        # Fallback: use basic yaml parsing
        import yaml
        data = yaml.safe_load(yaml_str)
        comments = _extract_comments_from_text(yaml_str)
        return data, comments
    
    yaml_parser = YAML()
    yaml_parser.preserve_quotes = True
    
    from io import StringIO
    data = yaml_parser.load(StringIO(yaml_str))
    
    comments = _extract_comments_from_ruamel(data, yaml_parser)
    
    return data, comments


def _extract_comments_from_ruamel(data: Any, yaml_parser: Any, path: Optional[List[str]] = None) -> List[CommentInfo]:
    """
    Extract comments from ruamel.yaml's CommentedMap/CommentedSeq structures.
    
    This is a simplified extraction - ruamel.yaml's comment structure is complex.
    For production use, we'd need more sophisticated traversal.
    """
    comments = []
    if path is None:
        path = []
    
    if isinstance(data, CommentedMap):
        # Get comments associated with this map
        ca = data.ca
        if ca:
            # Extract comments before items
            if hasattr(ca, 'items') and ca.items:
                for key, value in data.items():
                    key_path = path + [str(key)]
                    # Get comment before this key
                    if key in ca.items:
                        item_ca = ca.items[key]
                        if item_ca:
                            # Extract comment text
                            if hasattr(item_ca, 'comment') and item_ca.comment:
                                comment_lines = item_ca.comment[1] if isinstance(item_ca.comment, tuple) else item_ca.comment
                                if comment_lines:
                                    for line in comment_lines:
                                        if line and line.value:
                                            comments.append(CommentInfo(
                                                text=line.value.strip(),
                                                comment_type='line',
                                                line_number=0,  # ruamel doesn't preserve line numbers easily
                                                key_path=key_path[:-1],
                                                associated_key=str(key)
                                            ))
                    
                    # Recursively extract from nested structures
                    nested_comments = _extract_comments_from_ruamel(value, yaml_parser, key_path)
                    comments.extend(nested_comments)
    
    elif isinstance(data, CommentedSeq):
        for i, item in enumerate(data):
            item_path = path + [str(i)]
            nested_comments = _extract_comments_from_ruamel(item, yaml_parser, item_path)
            comments.extend(nested_comments)
    
    elif isinstance(data, dict):
        # Regular dict - recurse
        for key, value in data.items():
            key_path = path + [str(key)]
            nested_comments = _extract_comments_from_ruamel(value, yaml_parser, key_path)
            comments.extend(nested_comments)
    
    elif isinstance(data, list):
        # Regular list - recurse
        for i, item in enumerate(data):
            item_path = path + [str(i)]
            nested_comments = _extract_comments_from_ruamel(item, yaml_parser, item_path)
            comments.extend(nested_comments)
    
    return comments


def _extract_comments_from_text(yaml_str: str) -> List[CommentInfo]:
    """
    Fallback: Extract comments by parsing the YAML text directly.
    
    This is used when ruamel.yaml is not available.
    """
    comments = []
    lines = yaml_str.split('\n')
    
    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        
        # Line comment (entire line is comment)
        if stripped.startswith('#'):
            comment_text = stripped[1:].strip()
            if comment_text:
                comments.append(CommentInfo(
                    text=comment_text,
                    comment_type='line',
                    line_number=line_num,
                    key_path=[],
                    associated_key=None
                ))
            continue
        
        # Inline comment
        if '#' in line:
            # Check if # is inside quotes
            in_quotes = False
            quote_char = None
            hash_pos = -1
            
            for i, char in enumerate(line):
                if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                elif char == '#' and not in_quotes:
                    hash_pos = i
                    break
            
            if hash_pos >= 0:
                before_hash = line[:hash_pos].rstrip()
                after_hash = line[hash_pos + 1:].strip()
                
                if after_hash:
                    # Try to extract associated key
                    associated_key = None
                    if ':' in before_hash:
                        import re
                        key_match = re.match(r'^(\s*)([A-Za-z0-9_]+)\s*:', before_hash)
                        if key_match:
                            associated_key = key_match.group(2)
                    
                    comments.append(CommentInfo(
                        text=after_hash,
                        comment_type='inline',
                        line_number=line_num,
                        key_path=[],
                        associated_key=associated_key
                    ))
    
    return comments

