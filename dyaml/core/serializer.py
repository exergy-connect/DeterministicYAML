"""
Deterministic YAML serialization.

This module provides serialization of Python data structures to
Deterministic YAML format, ensuring canonical output.
"""

import sys
from pathlib import Path
from typing import Any

# Add lib directory to path to import existing DeterministicYAML
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'lib'))

try:
    from deterministic_yaml import DeterministicYAML
except ImportError:
    # Fallback if not available
    DeterministicYAML = None


def to_deterministic_yaml(data: Any) -> str:
    """
    Serialize Python data structure to Deterministic YAML string.
    
    Args:
        data: Python data structure (dict, list, scalar)
        
    Returns:
        Deterministic YAML string
    """
    if DeterministicYAML:
        return DeterministicYAML.to_deterministic_yaml(data)
    else:
        # Fallback implementation (simplified)
        import yaml
        return yaml.dump(data, sort_keys=True, default_flow_style=False, allow_unicode=True)

