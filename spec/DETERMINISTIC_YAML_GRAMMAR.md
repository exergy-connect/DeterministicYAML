# Deterministic YAML Formal Grammar

This document defines the formal grammar for Deterministic YAML using BNF-style notation.

## Important Note

**Deterministic YAML is valid YAML** - this grammar defines a subset of YAML syntax. Any standard YAML parser can parse Deterministic YAML correctly. The grammar is provided for reference and to ensure deterministic generation, but you don't need a special parser to read Deterministic YAML.

## Grammar Definition

```
# Entry point --------------------------------------------------------------

yaml ::= element(0)

# Elements ----------------------------------------------------------------

element(indent) ::= mapping(indent)
                  | list(indent)
                  | scalar

# Mapping -----------------------------------------------------------------

mapping(indent) ::= pair(indent)
                  | pair(indent) mapping(indent)

pair(indent) ::= INDENT(indent) key ":" SP value(indent + 1)

key ::= IDENT

value(indent) ::= scalar
                 | mapping(indent)
                 | list(indent)

# Lists -------------------------------------------------------------------

list(indent) ::= list_item(indent)
               | list_item(indent) list(indent)

list_item(indent) ::= INDENT(indent) "-" SP list_value(indent + 1)

list_value(indent) ::= scalar
                      | mapping(indent)
                      | list(indent)

# Scalars -----------------------------------------------------------------

scalar ::= IDENT
         | QUOTED
         | NUMBER
         | BOOLEAN
         | NULL

IDENT ::= /[A-Za-z0-9_]+/

QUOTED ::= "\"" QUOTED_CHAR* "\""

QUOTED_CHAR ::= /[^"\\]/ | ESCAPE

ESCAPE ::= "\\n"
         | "\\t"
         | "\\r"
         | "\\\\"
         | "\\\""

NUMBER ::= /-?[0-9]+/

BOOLEAN ::= "true" | "false"

NULL ::= "null"

# Indentation --------------------------------------------------------------

# indent() expands to exactly (indent * 2) spaces.
INDENT(0) ::= ""
INDENT(n) ::= "  " INDENT(n - 1)

SP ::= " "

# Comments -----------------------------------------------------------------

# EXPLICITLY FORBIDDEN: The '#' character is not part of the grammar.
# Comments are not allowed in Deterministic YAML.
# 
# Formal Rule: Comments are strictly forbidden. The '#' character may not
# appear in Deterministic YAML except as part of a quoted string value.
#
# Sanctioned Alternative: Use _comment key-value pairs for documentation.
# Example:
#   _comment: "This is documentation"
#   name: John
#
# The _comment field is a regular key-value pair, sorted lexicographically
# like any other key. Multiple _comment fields are allowed but not recommended.

# End ----------------------------------------------------------------------
```

## Grammar Rules Explained

### Entry Point

- `yaml` is the root production
- Must start at indent level 0
- Can be a mapping, list, or scalar

### Elements

An element at a given indent level can be:
- A mapping (key-value pairs)
- A list (sequence of items)
- A scalar (primitive value)

### Mappings

- One or more pairs
- Each pair: `INDENT key: SP value`
- Keys must be IDENT (unquoted identifiers)
- Values can be scalars, nested mappings, or lists

### Lists

- One or more list items
- Each item: `INDENT - SP value`
- Values can be scalars, nested mappings, or nested lists

### Scalars

Five types:
1. **IDENT**: Unquoted identifier `[A-Za-z0-9_]+`
2. **QUOTED**: Double-quoted string with escape sequences
3. **NUMBER**: Integer `-?[0-9]+`
4. **BOOLEAN**: `true` or `false` (lowercase)
5. **NULL**: `null`

### Indentation

- Indent level 0 = no spaces
- Indent level n = exactly `2 * n` spaces
- Always 2 spaces per level (no tabs)

## Examples

### Valid Deterministic YAML

**Mapping:**
```yaml
name: John
age: 30
```

**List:**
```yaml
- item1
- item2
```

**Nested:**
```yaml
config:
  host: localhost
  port: 5432
tags:
  - dev
  - ops
```

**Scalars:**
```yaml
name: John
count: 42
active: true
value: null
description: "A quoted string"
```

### Invalid (Not in Grammar)

- `name: "John"` when `John` matches IDENT (should be unquoted)
- `tags: [a, b]` (inline lists not in grammar)
- `{key: value}` (flow style not in grammar)
- `key: |` (multi-line strings not in grammar)
- `# comment` (comments **explicitly forbidden** - not in grammar)
- `key: value  # inline comment` (inline comments **explicitly forbidden**)
- `key: ~` (null must be `null`, not `~`)

**Note on Comments**: The `#` character is not part of the Deterministic YAML grammar. Comments are explicitly forbidden. Use `_comment: "documentation"` key-value pairs instead.

## Parser Implementation

See `deterministic_yaml_parser.py` for a parser implementation based on this grammar.

