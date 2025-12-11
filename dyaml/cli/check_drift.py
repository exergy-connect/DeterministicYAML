"""
dyaml check-drift command - Detect semantic drift in Deterministic YAML.
"""

import click
from pathlib import Path
import sys
import yaml

from rich.console import Console
from rich.table import Table


@click.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--baseline', type=click.Path(exists=True),
              help='Baseline file to compare against')
@click.option('--human-only', is_flag=True,
              help='Only check $human$ field integrity')
def check_drift(file: str, baseline: str, human_only: bool):
    """
    Detect semantic drift in Deterministic YAML files.
    
    Checks for:
    - Changes to $human$ fields
    - Value changes that contradict $human$ explanations
    - Unexpected modifications
    
    Useful for catching AI hallucinations and unintended changes.
    
    Examples:
    
        # Check against baseline
        dyaml check-drift config.d.yaml --baseline original.d.yaml
        
        # Only check $human$ fields
        dyaml check-drift config.d.yaml --baseline original.d.yaml --human-only
    """
    console = Console()
    
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if baseline:
            with open(baseline, 'r', encoding='utf-8') as f:
                baseline_data = yaml.safe_load(f)
            
            drift = _detect_drift(data, baseline_data, human_only)
            
            if drift['has_drift']:
                console.print("[yellow]⚠ Drift detected:[/yellow]")
                console.print()
                
                if drift['changed_values']:
                    console.print("[bold]Changed values:[/bold]")
                    for change in drift['changed_values']:
                        console.print(f"  {change['path']}: {change['before']} → {change['after']}")
                    console.print()
                
                if drift['human_changes']:
                    console.print("[bold]Modified $human$ fields:[/bold]")
                    for change in drift['human_changes']:
                        console.print(f"  {change['path']}.$human$:")
                        console.print(f"    - Before: {change['before']}")
                        console.print(f"    + After: {change['after']}")
                    console.print()
                
                # Check for contradictions
                if drift['contradictions']:
                    console.print("[red]Warning: Value changes contradict original $human$ reasoning![/red]")
                    for contradiction in drift['contradictions']:
                        console.print(f"  {contradiction['path']}: {contradiction['message']}")
                    console.print()
                
                sys.exit(1)
            else:
                console.print("[green]✓ No drift detected[/green]")
                sys.exit(0)
        else:
            # Single file check - validate $human$ fields are present and meaningful
            warnings = _check_human_fields(data)
            
            if warnings:
                console.print("[yellow]⚠ Warnings:[/yellow]")
                for warning in warnings:
                    console.print(f"  {warning}")
                sys.exit(1)
            else:
                console.print("[green]✓ $human$ fields look good[/green]")
                sys.exit(0)
                
    except Exception as e:
        console.print(f"[red]Error checking drift: {e}[/red]", err=True)
        sys.exit(1)


def _detect_drift(data: dict, baseline: dict, human_only: bool) -> dict:
    """Detect drift between current and baseline data."""
    drift = {
        'has_drift': False,
        'changed_values': [],
        'human_changes': [],
        'contradictions': []
    }
    
    _compare_for_drift(data, baseline, [], drift, human_only)
    
    drift['has_drift'] = bool(
        drift['changed_values'] or
        drift['human_changes'] or
        drift['contradictions']
    )
    
    return drift


def _compare_for_drift(d1: dict, d2: dict, path: list, drift: dict, human_only: bool):
    """Recursively compare for drift."""
    all_keys = set(d1.keys()) | set(d2.keys())
    
    for key in all_keys:
        key_path = path + [str(key)]
        path_str = '.'.join(key_path)
        
        if key not in d1:
            if not human_only:
                drift['changed_values'].append({
                    'path': path_str,
                    'before': None,
                    'after': d2[key]
                })
        elif key not in d2:
            if not human_only:
                drift['changed_values'].append({
                    'path': path_str,
                    'before': d1[key],
                    'after': None
                })
        elif key == '$human$':
            if d1[key] != d2[key]:
                drift['human_changes'].append({
                    'path': '.'.join(path),
                    'before': d1[key],
                    'after': d2[key]
                })
        elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
            _compare_for_drift(d1[key], d2[key], key_path, drift, human_only)
        elif isinstance(d1[key], list) and isinstance(d2[key], list):
            if d1[key] != d2[key] and not human_only:
                drift['changed_values'].append({
                    'path': path_str,
                    'before': d1[key],
                    'after': d2[key]
                })
        elif d1[key] != d2[key]:
            if not human_only:
                drift['changed_values'].append({
                    'path': path_str,
                    'before': d1[key],
                    'after': d2[key]
                })
            
            # Check for contradiction with $human$ field
            if isinstance(d1, dict) and '$human$' in d1:
                # Check if value change contradicts human explanation
                human_explanation = d1.get('$human$', '')
                if human_explanation and _contradicts(human_explanation, d1[key], d2[key]):
                    drift['contradictions'].append({
                        'path': path_str,
                        'message': f"Value change contradicts: {human_explanation}"
                    })


def _contradicts(explanation: str, old_value: any, new_value: any) -> bool:
    """Check if value change contradicts human explanation."""
    # Simple heuristic: if explanation mentions the old value or reason for it,
    # and the value changed, it might be a contradiction
    explanation_lower = explanation.lower()
    old_str = str(old_value).lower()
    
    # If explanation mentions the old value or a reason for it, and value changed
    if old_str in explanation_lower and old_value != new_value:
        return True
    
    return False


def _check_human_fields(data: dict) -> list:
    """Check if $human$ fields are present and meaningful."""
    warnings = []
    
    def check_recursive(obj, path):
        if isinstance(obj, dict):
            if '$human$' not in obj and obj:
                # Non-empty dict without $human$ - might want one
                warnings.append(f"{'.'.join(path)}: Consider adding $human$ field for documentation")
            
            for key, value in obj.items():
                if key != '$human$':
                    check_recursive(value, path + [str(key)])
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_recursive(item, path + [str(i)])
    
    check_recursive(data, [])
    
    return warnings

