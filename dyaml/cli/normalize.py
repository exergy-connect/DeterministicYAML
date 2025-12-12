"""
dyaml normalize command - Canonicalize Deterministic YAML files.

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
@click.option('--add-crc32', is_flag=True, default=False,
              help='Add CRC32 checksums to $human$ fields (default: False)')
def normalize(files: tuple, in_place: bool, check: bool, preserve_comments: bool, add_crc32: bool):
    """
    Normalize YAML files to canonical Deterministic YAML form.
    
    Works on both regular YAML and Deterministic YAML files. Ensures:
    - Keys are lexicographically sorted
    - $human$ fields are positioned first
    - Consistent formatting and indentation
    
    The operation is idempotent: normalize(normalize(x)) == normalize(x)
    
    Examples:
    
        # Normalize and output to stdout
        dyaml normalize config.yaml
        
        # Normalize in place
        dyaml normalize config.yaml --in-place
        
        # Check if normalized (useful for CI)
        dyaml normalize --check config.yaml
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
            deterministic_data = convert_yaml_to_deterministic(data, comments, preserve_comments, add_crc32)
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

