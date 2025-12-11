# Deterministic YAML CLI Tool Usage

The `dyaml` CLI tool provides production-ready commands for working with Deterministic YAML files in CI/CD pipelines.

## Installation

```bash
# From repository
pip install -e .

# Or install from PyPI (when published)
pip install deterministic-yaml
```

## Commands

### `dyaml convert` - Convert Standard YAML to Deterministic YAML

Convert standard YAML files to Deterministic YAML format, preserving comments as `$human$` fields.

**Usage:**

```bash
# Convert single file to stdout
dyaml convert config.yaml

# Convert to specific output file
dyaml convert config.yaml -o config.d.yaml

# Batch convert multiple files
dyaml convert *.yaml -o configs/

# Replace original with .d.yaml extension
dyaml convert config.yaml --in-place

# Strip comments (canonical mode)
dyaml convert config.yaml --no-preserve-comments
```

**Options:**
- `-o, --output`: Output file or directory
- `--in-place`: Replace original file with .d.yaml extension
- `--preserve-comments / --no-preserve-comments`: Preserve comments as `$human$` fields (default: True)
- `-v, --verbose`: Show detailed conversion progress

**Example:**

```bash
# Input: config.yaml
# Production config
database:
  host: db.example.com
  port: 5432

# Run
$ dyaml convert config.yaml

# Output:
database:
  $human$: "Production config"
  host: db.example.com
  port: 5432
```

### `dyaml validate` - Validate Deterministic YAML

Check if files conform to the Deterministic YAML specification.

**Usage:**

```bash
# Validate single file
dyaml validate config.d.yaml

# Validate multiple files
dyaml validate configs/*.d.yaml

# Stricter validation
dyaml validate --strict config.d.yaml

# JSON output for CI
dyaml validate --json config.d.yaml
```

**Options:**
- `--strict`: Perform stricter validation checks
- `--json`: Output results as JSON
- `-v, --verbose`: Show detailed validation information

**Exit Codes:**
- `0`: All files valid
- `1`: One or more files invalid

**Example JSON Output:**

```json
{
  "valid": false,
  "files": [
    {
      "file": "config.d.yaml",
      "valid": false,
      "errors": [
        {
          "line": 3,
          "message": "Keys not in lexicographic order",
          "severity": "error"
        }
      ],
      "warnings": []
    }
  ]
}
```

### `dyaml normalize` - Canonicalize Deterministic YAML

Normalize files to canonical form (idempotent operation).

**Usage:**

```bash
# Normalize and output to stdout
dyaml normalize config.d.yaml

# Normalize in place
dyaml normalize config.d.yaml --in-place

# Check if normalized (useful for CI)
dyaml normalize --check config.d.yaml
```

**Options:**
- `--in-place`: Modify files in place
- `--check`: Check if files are normalized (exit 1 if not)
- `--preserve-comments / --no-preserve-comments`: Preserve `$human$` fields (default: True)

**Exit Codes:**
- `0`: Files are normalized (or check passed)
- `1`: Files are not normalized (when using --check)

### `dyaml diff` - Compare Deterministic YAML Files

Show semantic differences between two files.

**Usage:**

```bash
# Compare two files
dyaml diff original.d.yaml modified.d.yaml

# Ignore $human$ changes
dyaml diff original.d.yaml modified.d.yaml --ignore-human

# JSON output
dyaml diff original.d.yaml modified.d.yaml --format json
```

**Options:**
- `--ignore-human`: Ignore changes to `$human$` fields
- `--format`: Output format (text or json)

**Example Output:**

```
⚠ Differences detected:

Changed values:
  database.max_connections: 50 → 100

Modified $human$ fields:
  database.$human$:
    - Before: "Max 50 due to memory constraints"
    + After: "Max 100 for better performance"
```

### `dyaml check-drift` - Detect Semantic Drift

Detect when files have drifted from baseline or have problematic changes.

**Usage:**

```bash
# Check against baseline
dyaml check-drift config.d.yaml --baseline original.d.yaml

# Only check $human$ fields
dyaml check-drift config.d.yaml --baseline original.d.yaml --human-only
```

**Options:**
- `--baseline`: Baseline file to compare against
- `--human-only`: Only check `$human$` field integrity

**Exit Codes:**
- `0`: No drift detected
- `1`: Drift detected

**Example Output:**

```
⚠ Drift detected:

Changed values:
  database.max_connections: 50 → 100

Modified $human$ fields:
  database.$human$:
    - Before: "Max 50 due to memory constraints"
    + After: "Max 100 for better performance"

Warning: Value change contradicts original $human$ reasoning!
  database.max_connections: Value change contradicts: Max 50 due to memory constraints
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Validate Deterministic YAML

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install deterministic-yaml
      - run: dyaml validate configs/*.d.yaml
      - run: dyaml normalize --check configs/*.d.yaml
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/exergy-connect/DeterministicYAML
    rev: v1.0.0
    hooks:
      - id: dyaml-validate
        name: Validate Deterministic YAML
        entry: dyaml validate
        language: python
        files: \.d\.yaml$
      
      - id: dyaml-normalize
        name: Normalize Deterministic YAML
        entry: dyaml normalize --check
        language: python
        files: \.d\.yaml$
```

### Exit Codes for CI

The CLI uses standard exit codes for CI/CD integration:

- `0`: Success
- `1`: Validation/check failed
- `2`: Invalid arguments
- `3`: File not found

## File Naming Convention

- **Standard YAML**: `*.yaml` or `*.yml`
- **Deterministic YAML**: `*.d.yaml`

The `.d.yaml` extension clearly signals that a file is in Deterministic YAML format, allowing both formats to coexist during migration.

## Examples

### Converting Existing Configs

```bash
# Convert all YAML configs to Deterministic YAML
dyaml convert configs/*.yaml -o configs/

# This creates:
# configs/database.d.yaml
# configs/api.d.yaml
# configs/cache.d.yaml
```

### Validating in CI

```bash
# In your CI script
if ! dyaml validate configs/*.d.yaml; then
    echo "Validation failed!"
    exit 1
fi
```

### Checking for Drift

```bash
# After LLM modifies config
dyaml check-drift config.d.yaml --baseline config.original.d.yaml

# Exit 1 if drift detected, allowing CI to fail
```

## Troubleshooting

### "ruamel.yaml not available"

If you see warnings about `ruamel.yaml` not being available, the tool will fall back to basic YAML parsing, which may lose some comment information. Install with:

```bash
pip install ruamel.yaml
```

### "Module not found: deterministic_yaml"

Make sure the `lib/` directory is in your Python path, or install the package in development mode:

```bash
pip install -e .
```

