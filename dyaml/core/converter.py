"""
Convert comments to $human$ fields in YAML data structures.

This module handles the deterministic conversion of YAML comments
into $human$ key-value pairs that preserve human context.
"""

from typing import Any, Dict, List, Optional
from .parser import CommentInfo


def consolidate_comments(comments: List[CommentInfo], key_path: List[str]) -> Optional[str]:
    """
    Consolidate comments for a specific object/key path into a single $human$ value.
    
    Args:
        comments: List of CommentInfo objects
        key_path: Path to the object (list of keys)
        
    Returns:
        Consolidated comment string, or None if no comments for this path
    """
    # Filter comments that belong to this path
    relevant_comments = []
    
    for comment in comments:
        # Check if comment belongs to this path
        if comment.key_path == key_path or (
            len(comment.key_path) == len(key_path) + 1 and
            comment.key_path[:-1] == key_path and
            comment.associated_key == key_path[-1] if key_path else None
        ):
            relevant_comments.append(comment)
    
    if not relevant_comments:
        return None
    
    # Consolidate comments with | delimiter
    parts = []
    for comment in relevant_comments:
        if comment.associated_key:
            # Inline comment associated with a key
            parts.append(f"{comment.associated_key}: {comment.text}")
        else:
            # Line comment
            parts.append(comment.text)
    
    return " | ".join(parts)


def add_human_fields(data: Any, comments: List[CommentInfo], path: Optional[List[str]] = None) -> Any:
    """
    Recursively add $human$ fields to data structure based on comments.
    
    Args:
        data: Python data structure
        comments: List of CommentInfo objects
        path: Current path in the data structure
        
    Returns:
        Data structure with $human$ fields added
    """
    if path is None:
        path = []
    
    if isinstance(data, dict):
        result = {}
        
        # Get consolidated comment for this object
        human_value = consolidate_comments(comments, path)
        if human_value:
            result['$human$'] = human_value
        
        # Process all keys
        for key, value in data.items():
            if key == '$human$':
                # Preserve existing $human$ field (merge if needed)
                existing_human = value
                if human_value:
                    # Merge: combine existing and new
                    result['$human$'] = f"{existing_human} | {human_value}" if existing_human else human_value
                else:
                    result['$human$'] = existing_human
            else:
                # Recursively process nested structures
                key_path = path + [str(key)]
                result[key] = add_human_fields(value, comments, key_path)
        
        return result
    
    elif isinstance(data, list):
        result = []
        for i, item in enumerate(data):
            item_path = path + [str(i)]
            result.append(add_human_fields(item, comments, item_path))
        return result
    
    else:
        # Scalar value - check for inline comments
        inline_comments = [
            c for c in comments
            if c.comment_type == 'inline' and
            c.key_path == path and
            c.associated_key is None
        ]
        
        if inline_comments:
            # This is a scalar with inline comment - add to parent
            # We'll handle this at the parent level
            return data
        
        return data


def convert_yaml_to_deterministic(
    data: Any,
    comments: List[CommentInfo],
    preserve_comments: bool = True
) -> Any:
    """
    Convert YAML data structure to deterministic format with $human$ fields.
    
    Args:
        data: Parsed YAML data
        comments: List of extracted comments
        preserve_comments: If True, add $human$ fields. If False, strip them.
        
    Returns:
        Data structure ready for deterministic serialization
    """
    if preserve_comments:
        return add_human_fields(data, comments)
    else:
        # Strip all $human$ fields
        return strip_human_fields(data)


def strip_human_fields(data: Any) -> Any:
    """
    Remove all $human$ fields from data structure.
    
    Args:
        data: Python data structure
        
    Returns:
        Data structure with all $human$ fields removed
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key != '$human$':
                result[key] = strip_human_fields(value)
        return result
    elif isinstance(data, list):
        return [strip_human_fields(item) for item in data]
    else:
        return data

