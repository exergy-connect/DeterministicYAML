"""
dyaml convert command - Convert standard YAML to Deterministic YAML.
"""

import click
from pathlib import Path
from typing import List, Optional
import sys

from ..core.parser import parse_yaml_with_comments, parse_yaml_string_with_comments
from ..core.converter import convert_yaml_to_deterministic
from ..core.serializer import to_deterministic_yaml


@click.command()
@click.argument('inputs', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file or directory')
@click.option('--in-place', is_flag=True, help='Replace original file with .d.yaml extension')
@click.option('--preserve-comments/--no-preserve-comments', default=True,
              help='Preserve comments as $human$ fields (default: True)')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed conversion progress')
def convert(inputs: tuple, output: str, in_place: bool, preserve_comments: bool, verbose: bool):
    """
    Convert standard YAML files to Deterministic YAML format.
    
    Converts one or more YAML files, preserving comments as $human$ fields.
    Output files use .d.yaml extension to signal Deterministic YAML format.
    
    Examples:
    
        # Convert single file to stdout
        dyaml convert config.yaml
        
        # Convert to specific output file
        dyaml convert config.yaml -o config.d.yaml
        
        # Batch convert multiple files
        dyaml convert *.yaml -o configs/
        
        # Replace original with .d.yaml extension
        dyaml convert config.yaml --in-place
    """
    input_paths = [Path(p) for p in inputs]
    
    # Determine output handling
    if in_place and output:
        click.echo("Error: Cannot use both --in-place and --output", err=True)
        sys.exit(2)
    
    if len(input_paths) == 1 and not output and not in_place:
        # Single file, output to stdout
        _convert_single_file(input_paths[0], None, preserve_comments, verbose)
    elif in_place:
        # Replace original files
        for input_path in input_paths:
            output_path = input_path.parent / f"{input_path.stem}.d.yaml"
            _convert_single_file(input_path, output_path, preserve_comments, verbose)
    elif output:
        # Output to specified file or directory
        output_path = Path(output)
        if output_path.is_dir() or (len(input_paths) > 1):
            # Batch mode: output to directory
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
            
            for input_path in input_paths:
                if output_path.is_dir():
                    output_file = output_path / f"{input_path.stem}.d.yaml"
                else:
                    output_file = output_path
                _convert_single_file(input_path, output_file, preserve_comments, verbose)
        else:
            # Single file output
            if len(input_paths) > 1:
                click.echo("Error: Multiple input files require directory output", err=True)
                sys.exit(2)
            _convert_single_file(input_paths[0], output_path, preserve_comments, verbose)
    else:
        click.echo("Error: Must specify --output or --in-place for multiple files", err=True)
        sys.exit(2)


def _convert_single_file(
    input_path: Path,
    output_path: Optional[Path],
    preserve_comments: bool,
    verbose: bool
):
    """Convert a single YAML file."""
    try:
        if verbose:
            click.echo(f"Converting {input_path}...", err=True)
        
        # Parse with comment preservation
        data, comments = parse_yaml_with_comments(str(input_path))
        
        # Convert to deterministic format
        deterministic_data = convert_yaml_to_deterministic(data, comments, preserve_comments)
        
        # Serialize to Deterministic YAML
        dyaml_str = to_deterministic_yaml(deterministic_data)
        
        # Output
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(dyaml_str)
            if verbose:
                click.echo(f"  → {output_path} ✓", err=True)
        else:
            # Output to stdout
            click.echo(dyaml_str)
            
    except Exception as e:
        click.echo(f"Error converting {input_path}: {e}", err=True)
        sys.exit(1)

