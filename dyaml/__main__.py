"""
CLI entry point for dyaml tool.

This allows running: python -m dyaml <command>
Or after installation: dyaml <command>
"""

import sys
import click
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from .cli.convert import convert
from .cli.validate import validate
from .cli.normalize import normalize
from .cli.diff import diff
from .cli.check_drift import check_drift


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    Deterministic YAML CLI Tool
    
    A production-ready CLI for converting, validating, and normalizing
    Deterministic YAML files in CI/CD pipelines.
    """
    pass


# Register all commands
cli.add_command(convert)
cli.add_command(validate)
cli.add_command(normalize)
cli.add_command(diff)
cli.add_command(check_drift)


if __name__ == '__main__':
    cli()

