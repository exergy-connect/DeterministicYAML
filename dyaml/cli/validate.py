"""
dyaml validate command - Validate Deterministic YAML files.
"""

import click
from pathlib import Path
import sys
import json

from ..core.validator import validate_file, ValidationResult
from rich.console import Console
from rich.table import Table


@click.command()
@click.argument('files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--strict', is_flag=True, help='Perform stricter validation checks')
@click.option('--json', 'json_output', is_flag=True, help='Output results as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation information')
def validate(files: tuple, strict: bool, json_output: bool, verbose: bool):
    """
    Validate Deterministic YAML files against the specification.
    
    Checks for:
    - Proper key ordering (lexicographic, $human$ first)
    - Correct indentation (2 spaces)
    - No flow style, anchors, or comments
    - Proper $human$ field positioning
    
    Exit codes:
    - 0: All files valid
    - 1: One or more files invalid
    
    Examples:
    
        # Validate single file
        dyaml validate config.d.yaml
        
        # Validate multiple files
        dyaml validate configs/*.d.yaml
        
        # JSON output for CI
        dyaml validate config.d.yaml --json
    """
    console = Console()
    file_paths = [Path(f) for f in files]
    
    all_valid = True
    results = []
    
    for file_path in file_paths:
        try:
            result = validate_file(str(file_path), strict)
            results.append((file_path, result))
            
            if not result.valid:
                all_valid = False
        except Exception as e:
            console.print(f"[red]Error validating {file_path}: {e}[/red]")
            all_valid = False
            results.append((file_path, None))
    
    # Output results
    if json_output:
        _output_json(results)
    else:
        _output_human_readable(results, console, verbose)
    
    # Exit with appropriate code
    sys.exit(0 if all_valid else 1)


def _output_json(results):
    """Output validation results as JSON."""
    output = {
        "valid": all(r[1] and r[1].valid for r in results if r[1]),
        "files": []
    }
    
    for file_path, result in results:
        file_info = {
            "file": str(file_path),
            "valid": result.valid if result else False
        }
        
        if result:
            file_info.update(result.to_dict())
        else:
            file_info["errors"] = [{"line": 0, "message": "Validation failed", "severity": "error"}]
            file_info["warnings"] = []
        
        output["files"].append(file_info)
    
    print(json.dumps(output, indent=2))


def _output_human_readable(results, console, verbose: bool):
    """Output validation results in human-readable format."""
    for file_path, result in results:
        if result is None:
            console.print(f"[red]✗[/red] Validation failed: {file_path}")
            continue
        
        if result.valid:
            if verbose:
                console.print(f"[green]✓[/green] Valid: {file_path}")
            else:
                console.print(f"[green]✓[/green] {file_path}")
        else:
            console.print(f"[red]✗[/red] Validation failed: {file_path}")
            
            # Show errors
            if result.errors:
                console.print("\n[red]Errors:[/red]")
                for error in result.errors:
                    console.print(f"  Line {error.line}: {error.message}")
            
            # Show warnings
            if result.warnings and verbose:
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  Line {warning.line}: {warning.message}")

