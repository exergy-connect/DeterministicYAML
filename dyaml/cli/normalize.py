"""
dyaml normalize command - Canonicalize Deterministic YAML files.
"""

import click
from pathlib import Path
import sys

from ..core.parser import parse_yaml_string_with_comments
from ..core.converter import convert_yaml_to_deterministic
from ..core.serializer import to_deterministic_yaml
from rich.console import Console


@click.command()
@click.argument('files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--in-place', is_flag=True, help='Modify files in place')
@click.option('--check', is_flag=True, help='Check if files are normalized (exit 1 if not)')
@click.option('--preserve-comments/--no-preserve-comments', default=True,
              help='Preserve $human$ fields (default: True)')
def normalize(files: tuple, in_place: bool, check: bool, preserve_comments: bool):
    """
    Normalize Deterministic YAML files to canonical form.
    
    Ensures:
    - Keys are lexicographically sorted
    - $human$ fields are positioned first
    - Consistent formatting and indentation
    
    The operation is idempotent: normalize(normalize(x)) == normalize(x)
    
    Examples:
    
        # Normalize and output to stdout
        dyaml normalize config.d.yaml
        
        # Normalize in place
        dyaml normalize config.d.yaml --in-place
        
        # Check if normalized (useful for CI)
        dyaml normalize --check config.d.yaml
    """
    console = Console()
    file_paths = [Path(f) for f in files]
    
    all_normalized = True
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse and convert
            data, comments = parse_yaml_string_with_comments(content)
            deterministic_data = convert_yaml_to_deterministic(data, comments, preserve_comments)
            normalized = to_deterministic_yaml(deterministic_data)
            
            if check:
                # Check if already normalized
                if content.strip() != normalized.strip():
                    console.print(f"[red]✗[/red] {file_path} is not normalized")
                    all_normalized = False
                else:
                    if len(file_paths) == 1:
                        console.print(f"[green]✓[/green] {file_path} is normalized")
            elif in_place:
                # Write back to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(normalized)
                console.print(f"[green]✓[/green] Normalized {file_path}")
            else:
                # Output to stdout
                if len(file_paths) > 1:
                    console.print(f"[dim]# {file_path}[/dim]")
                click.echo(normalized)
                if len(file_paths) > 1:
                    console.print()  # Blank line between files
                    
        except Exception as e:
            console.print(f"[red]Error normalizing {file_path}: {e}[/red]", err=True)
            sys.exit(1)
    
    if check:
        sys.exit(0 if all_normalized else 1)

