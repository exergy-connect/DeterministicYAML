# Formal Rule: Comments in Deterministic YAML

## Rule Statement

**Comments are explicitly forbidden in Deterministic YAML.**

The YAML comment syntax (`#`) is not part of the Deterministic YAML grammar and may not appear in Deterministic YAML documents except as part of a quoted string value.

## Formal Definition

### Prohibition

The `#` character is **not** a valid token in Deterministic YAML grammar, except when it appears inside a double-quoted string value.

**Forbidden forms:**
- Line comments: `# This is a comment`
- Inline comments: `key: value  # comment`
- Block comments: Multiple consecutive `#` lines
- Any occurrence of `#` outside quoted strings

### Grammar Exclusion

In the formal grammar (BNF/GBNF), comments are explicitly excluded:

```
# Comments are not part of the grammar
# The '#' character is not defined as a production rule
# There is no COMMENT ::= "#" ... rule
```

The grammar defines only:
- Mappings (key-value pairs)
- Lists (sequences)
- Scalars (values)
- Whitespace and indentation

**Comments are not a production rule.**

## Sanctioned Alternative: `_comment` Fields

When documentation is needed, use a `_comment` key-value pair:

```yaml
_comment: "This is documentation"
name: John
age: 30
```

### Rules for `_comment` Fields

1. **Key**: Must be exactly `_comment` (underscore prefix indicates metadata)
2. **Value**: Must be a quoted string (since it typically contains spaces/punctuation)
3. **Treatment**: `_comment` is a regular key-value pair, sorted lexicographically
4. **Multiple**: Multiple `_comment` fields are allowed but not recommended
5. **Nested**: `_comment` can appear at any nesting level

### Examples

**Simple comment:**
```yaml
_comment: "User profile"
name: John
age: 30
```

**Nested comments:**
```yaml
_comment: "Main configuration"
config:
  _comment: "Database settings"
  host: localhost
  port: 5432
```

**Multiple comments (not recommended but valid):**
```yaml
_comment: "Top-level documentation"
name: John
_comment2: "Additional note"  # Valid but not recommended
age: 30
```

## Rationale

### Why Forbid Comments?

1. **Variance**: Same logical data can have different comments
   ```yaml
   # Version 1
   name: John
   
   # Version 2 (different comment, same data)
   name: John  # User name
   ```

2. **Non-deterministic**: Comments break canonical representation
   - Same data → different YAML (due to comments)
   - Breaks determinism requirement

3. **LLM Entropy**: Comments create branching points
   - Model must decide: include comment? What comment?
   - Increases output variance

4. **Parsing Ambiguity**: Comments can be ambiguous
   - Inline comments: `key: value # comment` - is `#` part of value?
   - Whitespace sensitivity

### Why `_comment` Fields?

1. **Deterministic**: Same data → same YAML (comments are part of data)
2. **Parseable**: Comments survive round-trip through any YAML parser
3. **Sortable**: Comments included in lexicographic key sorting
4. **Explicit**: Clear, unambiguous syntax
5. **LLM-friendly**: No ambiguity about where/how to include documentation

## Validation

A Deterministic YAML validator must:

1. **Reject** any occurrence of `#` outside quoted strings
2. **Accept** `_comment` fields as regular key-value pairs
3. **Report** line numbers where `#` appears

### Validation Example

```python
from lib.deterministic_yaml import DeterministicYAML

yaml_text = """
# This is a comment (INVALID)
name: John
age: 30  # inline comment (INVALID)
"""

is_valid, error = DeterministicYAML.validate(yaml_text)
# Returns: (False, "Line 2: Comments not allowed; Line 3: Comments not allowed")
```

## GBNF Grammar Reflection

The GBNF grammar (`deterministic_yaml.gbnf`) explicitly excludes comments:

- No `COMMENT` production rule
- No `#` token definition
- Grammar only defines: mappings, lists, scalars, whitespace

The grammar comment section states:
```
# Comments are EXPLICITLY FORBIDDEN
# The '#' character is not part of this grammar.
# Use _comment key-value pairs for documentation instead.
```

## Implementation

### Parser Behavior

A Deterministic YAML parser must:
- **Reject** input containing `#` outside quoted strings
- **Accept** `_comment` as a valid key (treated like any other key)
- **Report** validation errors with line numbers

### Normalizer Behavior

A Deterministic YAML normalizer must:
- **Remove** all comments (lines starting with `#`, inline `# comment`)
- **Preserve** data structure
- **Optionally convert** comments to `_comment` fields (if requested)

## Summary

| Aspect | Standard YAML | Deterministic YAML |
|--------|---------------|-----------------|
| Comments | Allowed (`#`) | **Forbidden** |
| Documentation | Comments | `_comment` fields |
| Determinism | Low (comments vary) | High (comments are data) |
| LLM-friendly | No (ambiguous) | Yes (explicit) |

**Formal Rule**: `#` is not a valid token in Deterministic YAML grammar. Use `_comment: "documentation"` for documentation needs.

