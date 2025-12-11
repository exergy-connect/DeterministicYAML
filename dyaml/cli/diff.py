"""
dyaml diff command - Compare Deterministic YAML files semantically.
"""

import click
from pathlib import Path
import sys
import json
import yaml

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax


@click.command()
@click.argument('file1', type=click.Path(exists=True))
@click.argument('file2', type=click.Path(exists=True))
@click.option('--ignore-human', is_flag=True, help='Ignore changes to $human$ fields')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text',
              help='Output format (default: text)')
def diff(file1: str, file2: str, ignore_human: bool, output_format: str):
    """
    Compare two Deterministic YAML files semantically.
    
    Shows differences in data structure, ignoring formatting.
    Highlights $human$ field changes separately.
    
    Examples:
    
        # Compare two files
        dyaml diff original.d.yaml modified.d.yaml
        
        # Ignore $human$ changes
        dyaml diff original.d.yaml modified.d.yaml --ignore-human
        
        # JSON output
        dyaml diff original.d.yaml modified.d.yaml --format json
    """
    console = Console()
    
    try:
        # Load both files
        with open(file1, 'r', encoding='utf-8') as f:
            data1 = yaml.safe_load(f)
        with open(file2, 'r', encoding='utf-8') as f:
            data2 = yaml.safe_load(f)
        
        # Compute differences
        differences = _compute_diff(data1, data2, ignore_human)
        
        if output_format == 'json':
            _output_json_diff(differences)
        else:
            _output_text_diff(differences, console, file1, file2)
            
    except Exception as e:
        console.print(f"[red]Error comparing files: {e}[/red]", err=True)
        sys.exit(1)


def _compute_diff(data1: dict, data2: dict, ignore_human: bool) -> dict:
    """Compute semantic differences between two data structures."""
    differences = {
        'changed_values': [],
        'added_keys': [],
        'removed_keys': [],
        'human_changes': []
    }
    
    _diff_dict(data1, data2, [], differences, ignore_human)
    
    return differences


def _diff_dict(d1: dict, d2: dict, path: list, differences: dict, ignore_human: bool):
    """Recursively compare two dictionaries."""
    all_keys = set(d1.keys()) | set(d2.keys())
    
    for key in all_keys:
        key_path = path + [str(key)]
        path_str = '.'.join(key_path)
        
        if key == '$human$' and ignore_human:
            continue
        
        if key not in d1:
            differences['added_keys'].append(path_str)
        elif key not in d2:
            differences['removed_keys'].append(path_str)
        elif key == '$human$':
            if d1[key] != d2[key]:
                differences['human_changes'].append({
                    'path': '.'.join(path),
                    'before': d1[key],
                    'after': d2[key]
                })
        elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
            _diff_dict(d1[key], d2[key], key_path, differences, ignore_human)
        elif isinstance(d1[key], list) and isinstance(d2[key], list):
            _diff_list(d1[key], d2[key], key_path, differences, ignore_human)
        elif d1[key] != d2[key]:
            differences['changed_values'].append({
                'path': path_str,
                'before': d1[key],
                'after': d2[key]
            })


def _diff_list(l1: list, l2: list, path: list, differences: dict, ignore_human: bool):
    """Compare two lists."""
    # Simple comparison: check if lists are equal
    if l1 != l2:
        differences['changed_values'].append({
            'path': '.'.join(path),
            'before': l1,
            'after': l2
        })


def _output_json_diff(differences: dict):
    """Output differences as JSON."""
    print(json.dumps(differences, indent=2, default=str))


def _output_text_diff(differences: dict, console: Console, file1: str, file2: str):
    """Output differences in human-readable format."""
    has_changes = any([
        differences['changed_values'],
        differences['added_keys'],
        differences['removed_keys'],
        differences['human_changes']
    ])
    
    if not has_changes:
        console.print("[green]Files are identical[/green]")
        return
    
    console.print(f"[yellow]⚠ Differences detected:[/yellow]")
    console.print()
    
    # Changed values
    if differences['changed_values']:
        console.print("[bold]Changed values:[/bold]")
        for change in differences['changed_values']:
            console.print(f"  {change['path']}: {change['before']} → {change['after']}")
        console.print()
    
    # Added keys
    if differences['added_keys']:
        console.print("[bold]Added keys:[/bold]")
        for key in differences['added_keys']:
            console.print(f"  + {key}")
        console.print()
    
    # Removed keys
    if differences['removed_keys']:
        console.print("[bold]Removed keys:[/bold]")
        for key in differences['removed_keys']:
            console.print(f"  - {key}")
        console.print()
    
    # $human$ changes
    if differences['human_changes']:
        console.print("[bold]Modified $human$ fields:[/bold]")
        for change in differences['human_changes']:
            console.print(f"  {change['path']}.$human$:")
            console.print(f"    - Before: {change['before']}")
            console.print(f"    + After: {change['after']}")
        console.print()

