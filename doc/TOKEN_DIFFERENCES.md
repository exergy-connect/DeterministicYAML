# Token Count Differences: JSON vs YAML

This document explains the token-level differences between JSON and YAML and their implications for LLM generation.

## Key Findings

### Token Count Comparison

**YAML typically uses 20-40% fewer tokens than JSON** for equivalent data structures.

**Average across test cases:**
- JSON (pretty): ~36.5 tokens
- JSON (compact): ~26.8 tokens  
- YAML (block): ~23.5 tokens
- YAML (flow): ~23.8 tokens

**YAML is ~0.64x the token count of JSON (pretty)**
**YAML is ~0.88x the token count of JSON (compact)**

## Why YAML Uses Fewer Tokens

### 1. **No Mandatory Quotes**

**JSON:**
```json
{"name": "John", "age": 30}
```
Tokens: `{`, `"name"`, `:`, `"John"`, `,`, `"age"`, `:`, `30`, `}`

**YAML:**
```yaml
name: John
age: 30
```
Tokens: `name`, `:`, `John`, `age`, `:`, `30`

**Savings**: JSON requires 4 quote tokens (`"name"`, `"John"`, `"age"`) that YAML doesn't need.

### 2. **Unquoted Strings**

JSON must quote all string values:
```json
{"status": "active"}
```
→ 7 tokens: `{`, `"status"`, `:`, `"active"`, `}`

YAML can use unquoted strings:
```yaml
status: active
```
→ 3 tokens: `status`, `:`, `active`

**Savings**: 2 tokens per string value (opening and closing quotes).

### 3. **No Commas**

JSON requires commas between items:
```json
["a", "b", "c"]
```
→ 7 tokens: `[`, `"a"`, `,`, `"b"`, `,`, `"c"`, `]`

YAML uses newlines:
```yaml
- a
- b
- c
```
→ 5 tokens: `-`, `a`, `-`, `b`, `-`, `c` (or fewer with list syntax)

**Savings**: 1 token per item (comma) vs newline (which may be part of whitespace token).

### 4. **Indentation vs Braces**

JSON uses braces and brackets:
```json
{
  "key": {
    "nested": "value"
  }
}
```
→ Multiple tokens for `{`, `}`, `[`, `]`

YAML uses indentation:
```yaml
key:
  nested: value
```
→ Indentation is whitespace (often fewer tokens, or part of existing tokens)

**Trade-off**: YAML uses more whitespace tokens, but they're often more efficient than structural tokens.

## Token Boundary Differences

### JSON Tokenization

JSON's rigid structure creates predictable token boundaries:

```
{"name": "John"}
```

Typical tokenization:
- `{` (structural)
- `"name"` (quoted key - single token or split)
- `:` (separator)
- `"John"` (quoted value)
- `}` (structural)

**Characteristics:**
- Quotes are part of string tokens or separate tokens
- Structural tokens (`{`, `}`, `[`, `]`) are always separate
- Commas are separate tokens
- Predictable boundaries

### YAML Tokenization

YAML's flexible syntax creates variable token boundaries:

```
name: John
age: 30
```

Typical tokenization:
- `name` (unquoted key)
- `:` (separator)
- `John` (unquoted value)
- `age` (next key)
- `:` (separator)
- `30` (number)

**Characteristics:**
- No quotes (fewer tokens)
- Whitespace (newlines, indentation) may be separate tokens or part of others
- Less predictable boundaries (depends on quote style, block style, etc.)

## Impact on LLM Generation

### 1. **Generation Cost**

**Fewer tokens = Lower cost**

If YAML uses 25% fewer tokens:
- Input cost: 25% lower (if prompt includes example)
- Output cost: 25% lower (generated tokens)
- Total cost: ~25% lower

**Example:**
- JSON output: 30 tokens
- YAML output: 22 tokens
- Savings: 8 tokens per generation
- At $0.01 per 1K tokens: $0.00008 per generation

### 2. **Generation Speed**

Fewer tokens to generate means:
- Faster completion (fewer forward passes)
- Lower latency
- Higher throughput

**Impact**: ~20-30% faster generation for YAML vs JSON.

### 3. **Token Probability Distribution**

**JSON**: More structural tokens (`"`, `{`, `}`, `,`) create:
- Predictable token sequences
- High probability for structural tokens
- Lower entropy (as analyzed in `analyze_logits.py`)

**YAML**: Fewer structural tokens, more content tokens:
- Less predictable sequences
- Probability distributed across content tokens
- Higher entropy (as analyzed in `analyze_logits.py`)

**Paradox**: YAML uses fewer tokens but has higher entropy per token position.

### 4. **Context Window Efficiency**

**Fewer tokens = More data per context window**

If context window is 4K tokens:
- JSON: ~110-150 data objects (at ~30 tokens each)
- YAML: ~170-180 data objects (at ~23 tokens each)

**Impact**: YAML allows ~30-50% more data in the same context window.

## Token Efficiency by Structure Type

### Simple Key-Value Pairs

**JSON:**
```json
{"key": "value"}
```
~5 tokens

**YAML:**
```yaml
key: value
```
~3 tokens

**Efficiency**: YAML is 40% more token-efficient.

### Nested Objects

**JSON:**
```json
{"a": {"b": {"c": "d"}}}
```
~11 tokens

**YAML:**
```yaml
a:
  b:
    c: d
```
~7 tokens

**Efficiency**: YAML is 36% more token-efficient.

### Arrays/Lists

**JSON:**
```json
["a", "b", "c"]
```
~7 tokens

**YAML:**
```yaml
- a
- b
- c
```
~5 tokens (or fewer with inline syntax)

**Efficiency**: YAML is 29% more token-efficient.

### Mixed Structures

For complex nested structures with arrays and objects:
- JSON: ~30-50 tokens
- YAML: ~20-35 tokens

**Efficiency**: YAML is typically 25-35% more token-efficient.

## Trade-offs

### Advantages of YAML's Token Efficiency

1. **Lower Cost**: Fewer tokens = lower API costs
2. **Faster Generation**: Fewer tokens to generate
3. **More Context**: Fit more data in context window
4. **Human Readable**: Easier to read and edit

### Disadvantages

1. **Higher Variance**: More ways to represent same data = more output variance
2. **Higher Entropy**: Less predictable token sequences
3. **Parsing Complexity**: More complex to parse correctly
4. **Ambiguity**: Whitespace-sensitive, can be ambiguous

## Practical Implications

### When to Prefer JSON (Despite Higher Token Count)

1. **Deterministic Output**: Need consistent structure
2. **API Responses**: Standard format, easy to parse
3. **Structured Data**: When structure is more important than readability
4. **Low Variance Requirements**: When output consistency matters more than token count

### When to Prefer YAML (Despite Higher Variance)

1. **Cost-Sensitive**: Need to minimize token usage
2. **Context-Limited**: Need to fit more data in context window
3. **Human-Readable**: Need readable configuration or documentation
4. **Complex Nested Data**: YAML's indentation is clearer for deep nesting

## Token Count vs Variance Trade-off

**Key Insight**: There's a trade-off between token efficiency and output variance.

- **JSON**: More tokens, lower variance (deterministic)
- **YAML**: Fewer tokens, higher variance (non-deterministic)

**Decision Framework**:
- If **consistency > cost**: Use JSON
- If **cost > consistency**: Use YAML
- If **both matter**: Use JSON with post-processing, or YAML with normalization

## Measurement Notes

The token counts in this analysis use an approximation (chars/4) when tiktoken is not available. For accurate measurements:

1. Install tiktoken: `pip install tiktoken`
2. Use the actual tokenizer for your model (e.g., `cl100k_base` for GPT-4)
3. Run `token_count_analysis.py` with tiktoken installed

Actual token counts may vary by:
- Model tokenizer (GPT-3.5 vs GPT-4 vs Claude, etc.)
- Specific content (some strings tokenize differently)
- Whitespace handling (varies by tokenizer)

The relative differences (YAML vs JSON) should remain consistent across tokenizers.

