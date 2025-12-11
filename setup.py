"""
Setup script for Deterministic YAML CLI tool.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

setup(
    name='deterministic-yaml',
    version='1.0.0',
    description='Deterministic YAML CLI tool for CI/CD pipelines',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Exergy ∞ LLC',
    author_email='',
    url='https://github.com/exergy-connect/DeterministicYAML',
    packages=find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=3.8',
    install_requires=[
        'click>=8.1.0',
        'ruamel.yaml>=0.18.0',
        'rich>=13.0.0',
        'pydantic>=2.0.0',
        'pyyaml>=6.0.2',
    ],
    entry_points={
        'console_scripts': [
            'dyaml=dyaml.__main__:cli',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup',
    ],
    keywords='yaml deterministic ci-cd llm',
)

