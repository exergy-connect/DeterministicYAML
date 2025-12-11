# Cursor Prompt: Deterministic YAML Mode

You must follow the Deterministic YAML Specification below whenever generating YAML.

Your goal is to produce deterministic, low-variance, LLM-friendly YAML with strict canonical formatting.

**This is a constrained format. Do not deviate.**

## Deterministic YAML Specification

### 1. Keys

- Keys must be unquoted ASCII identifiers: `[A-Za-z0-9_]+`
- If a key does not match this pattern, the output is invalid.
- Always end keys with a colon.

### 2. String Values

- Unquoted strings are allowed only if they match the same safe identifier pattern: `[A-Za-z0-9_]+`
- All other strings must be double-quoted.
- Strings that contain whitespace, punctuation, special characters, or resemble numbers must be double-quoted.
- Empty string must be: `""`

### 3. Numbers

- Allowed numeric format: integers matching `^-?[0-9]+$`
- Anything else must be quoted.

### 4. Booleans and Null

- Boolean values: `true` or `false` (lowercase only)
- Null: `null` only
- Bare keys without values are never allowed.

### 5. Lists

- Always block style:
  ```yaml
  key:
    - value
    - value
  ```
- Never inline lists.
- Indentation must be exactly 2 spaces.

### 6. Objects

- Always block style.
- 2-space indentation for all nested mappings.

### 7. Multi-line Strings

- Forbidden.
- If needed, use `\n` inside a double-quoted string.

### 8. Comments - Explicitly Forbidden

**Formal Rule: Comments are strictly forbidden in Deterministic YAML.**

- **YAML comment syntax (`#`) is not allowed anywhere**
- This includes line comments, inline comments, and block comments
- **Rationale**: Comments introduce variance - same data, different comments = non-deterministic

**Sanctioned Alternative: Use `_comment` key-value pairs**

When documentation is needed:
```yaml
_comment: "This is documentation"
name: John
age: 30
```

Rules for `_comment`:
- Key must be exactly `_comment`
- Value must be a quoted string
- Treated as regular key-value pair (sorted lexicographically)
- Multiple `_comment` fields allowed but not recommended

### 9. Anchors & Aliases

- Forbidden.

### 10. Document Markers

- Forbidden. No `---` or `...`.

### 11. Key Ordering

- Keys must be sorted lexicographically at every level.

## Formatting Rules

- Use only 2 spaces for indentation.
- No tabs.
- No trailing spaces.
- No blank lines unless explicitly required (generally avoid them).
- One canonical representation per data structure.

## Your Tasks

Whenever the user requests YAML, you must:

1. **Validate** that the output adheres to every rule above.
2. **Normalize** the structure:
   - Sort keys lexicographically
   - Quote unsafe strings
   - Convert illegal formats
3. **Emit** only Deterministic YAML with no commentary or explanation.

If the user asks for overflowing or complex YAML features, convert them into the closest valid Deterministic YAML structure.

If the user provides YAML that violates the spec, normalize it automatically.

## Output Expectations

- Absolutely no prose mixed with YAML unless explicitly asked.
- Absolutely no non-canonical variants.
- Consistency is more important than human readability.
- If a structure cannot be expressed canonically, fall back to quoting.

## Example (canonical)

**Input:**
```yaml
name: John
age: 30
active: yes
tags: [dev, ops]
```

**Output (deterministic YAML):**
```yaml
active: true
age: 30
name: John
tags:
  - dev
  - ops
```

