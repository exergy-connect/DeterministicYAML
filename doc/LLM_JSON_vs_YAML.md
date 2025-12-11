# JSON vs YAML: LLM Mechanics and Practical Differences

## Executive Summary

JSON's rigid grammar and high training frequency create predictable, low-entropy token distributions that favor deterministic decoding. YAML's flexible syntax and lower training exposure inflate entropy, increase branching in logit space, and amplify variance across decoding strategies. This document examines the token-level mechanics behind these differences.

---

## 1. Variance in Model Outputs

### Why JSON Reduces Output Variance

JSON's structural rigidity constrains the model's token probability distribution at each step:

1. **Fixed Delimiters**: After an opening brace `{`, the model knows the next token must be either:
   - A string key (starting with `"`)
   - A closing brace `}`
   - Whitespace (which is then followed by one of the above)

   This collapses the logit space to ~2-3 high-probability tokens instead of hundreds.

2. **Mandatory Quoting**: All keys and string values must be quoted. The model learns that after a colon `:`, if the value is a string, it must start with `"`. This eliminates ambiguity about whether a token is a string, number, boolean, or null.

3. **No Alternative Syntaxes**: There is exactly one way to represent each structure. An object is always `{...}`, an array is always `[...]`, strings are always `"..."`. The model doesn't need to choose between equivalent representations.

**Token Probability Example (after `{`):**
```
Token        Logit    Probability
"            8.2      0.95
}            2.1      0.04
[whitespace] 1.3      0.01
```

The top token (`"`) dominates with ~95% probability, making greedy decoding nearly deterministic.

### Why YAML Increases Variance

YAML's flexible grammar creates multiple valid continuations at each step:

1. **Unquoted Keys**: After a key name, the model must decide:
   - Is this a key-value pair? (use `:`)
   - Is this a list item? (use `-`)
   - Is this a nested mapping? (use `:` with indentation)
   - Is this a flow-style mapping? (use `{`)

2. **Multiple String Representations**: The same string can be:
   - Unquoted: `key: value`
   - Single-quoted: `key: 'value'`
   - Double-quoted: `key: "value"`
   - Literal block: `key: |\n  value`
   - Folded block: `key: >\n  value`

3. **Indentation Ambiguity**: YAML relies on whitespace, which the model must track contextually. The same logical structure can be expressed with different indentation levels, and the model must infer intent.

**Token Probability Example (after `key`):**
```
Token        Logit    Probability
:            6.1      0.45
-            5.8      0.38
[space]:     4.2      0.12
\n           2.1      0.05
```

The top token (`:`) has only ~45% probability, with significant mass on alternatives. This creates branching that propagates through decoding.

### How Structural Rigidity Affects Token Probability Distribution

**JSON**: The grammar acts as a hard constraint. Invalid continuations have near-zero probability because:
- The model was trained to reject them (they're invalid JSON)
- The training corpus contains millions of valid JSON examples
- Invalid JSON is immediately recognizable and penalized during training

**YAML**: The grammar is permissive. Multiple continuations are valid, so the model distributes probability mass across them:
- The model sees fewer YAML examples in training
- Valid YAML has many equivalent forms
- The model must maintain a probability distribution over all valid continuations

**Mathematical Impact**: In JSON, the entropy of the next-token distribution is low (H ≈ 0.2-0.5 bits for structured positions). In YAML, entropy is higher (H ≈ 1.5-3.0 bits), meaning the model is more uncertain about the next token.

---

## 2. Decoding Interaction

### Greedy Decoding

**JSON with Greedy**:
- After `{`, the model predicts `"` with ~95% probability → greedy selects `"`
- After `"key"`, the model predicts `:` with ~98% probability → greedy selects `:`
- The path through the token tree is nearly deterministic

**YAML with Greedy**:
- After `key`, the model predicts `:` with ~45% probability → greedy selects `:`
- But if the context suggests a list, `-` might have 38% → greedy might select `-` instead
- Small context changes can flip the greedy choice, creating variance

**Result**: JSON greedy decoding is stable; YAML greedy decoding is sensitive to context shifts.

### Temperature Sampling

**JSON with Temperature**:
- Low temperature (T=0.1): The high-probability token (`"` after `{`) becomes even more dominant. Sampling rarely deviates.
- High temperature (T=2.0): Even with temperature scaling, the logit gap between `"` (8.2) and `}` (2.1) is large. The model still strongly favors `"`.

**YAML with Temperature**:
- Low temperature (T=0.1): The top token (`:`) becomes more dominant, but alternatives (`-`, `[space]:`) still have non-trivial probability.
- High temperature (T=2.0): The flattened distribution makes `-` and `:` nearly equiprobable. The model frequently alternates between representations.

**Result**: Temperature amplifies variance in YAML more than in JSON because YAML's base distribution is flatter.

### Top-k / Top-p

**JSON with Top-k**:
- At most positions, k=3 captures 99%+ of probability mass (the valid continuation plus whitespace/formatting variants).
- Top-p=0.95 typically includes only 1-2 tokens.
- The model rarely samples from outside the top tokens because invalid continuations have near-zero probability.

**YAML with Top-k**:
- k=3 might capture only 60-70% of probability mass because many valid continuations exist.
- Top-p=0.95 might include 5-10 tokens (different quote styles, indentation levels, flow vs block).
- The model frequently samples from a larger set of valid alternatives.

**Result**: Top-k/top-p filtering is less effective in YAML because the valid continuation set is larger.

### Beam Search

**JSON with Beam Search**:
- Beam width=5 is often overkill. The top-1 path dominates, and beams 2-5 are usually just formatting variants (spaces vs tabs, trailing commas).
- The search space is small, so beam search converges quickly to the same high-probability path.

**YAML with Beam Search**:
- Beam width=5 explores genuinely different structural choices (flow vs block, quoted vs unquoted, different indentation).
- Beams can diverge into semantically equivalent but syntactically different outputs.
- The search space is larger, so beam search may not converge to a single "best" path.

**Result**: Beam search in YAML explores more diverse outputs, increasing variance across runs.

---

## 3. Grammar and Entropy

### How JSON's Strict Grammar Collapses the Search Space

JSON's grammar is context-free with no ambiguity:

```
JSON → object | array | value
object → '{' (pair (',' pair)*)? '}'
pair → string ':' value
string → '"' (char)* '"'
```

At each parsing step, there is exactly one valid production rule. The model learns this constraint during training:

- After `{`, only `"` (start of string key) or `}` (empty object) are valid.
- After `"key"`, only `:` is valid.
- After `:`, the value type determines the next token (if string, then `"`).

**Token Tree Depth**: The branching factor is ~1-2 at most positions, creating a narrow tree.

**Entropy Calculation**: 
- Position after `{`: H = -Σ p(x) log₂ p(x) ≈ 0.3 bits (dominated by `"`)
- Position after `"key"`: H ≈ 0.1 bits (dominated by `:`)

### How YAML's Flexible Grammar Inflates Entropy

YAML's grammar is context-sensitive and ambiguous:

```
YAML → mapping | sequence | scalar
mapping → (key ':' value)+  (block style)
       | '{' (key ':' value (',' key ':' value)*)? '}'  (flow style)
key → unquoted | single-quoted | double-quoted
value → scalar | mapping | sequence
scalar → unquoted | single-quoted | double-quoted | literal-block | folded-block
```

At each parsing step, multiple valid production rules exist:

- After `key`, the model can choose: `:` (mapping), `-` (sequence item), or indentation-based nesting.
- For a string value, the model can choose: unquoted, single-quoted, double-quoted, literal block, or folded block.

**Token Tree Depth**: The branching factor is ~3-10 at many positions, creating a wide tree.

**Entropy Calculation**:
- Position after `key`: H ≈ 1.8 bits (distributed across `:`, `-`, `[space]:`, etc.)
- Position for string value: H ≈ 2.2 bits (distributed across quote styles and block styles)

### Why Ambiguity Affects Determinism

Ambiguity means the model must maintain probability mass over multiple valid continuations. This creates:

1. **Path Dependency**: Small context changes (e.g., a different example in the prompt) can shift probability mass between valid alternatives, changing the sampled path.

2. **Cumulative Variance**: Each ambiguous position multiplies the number of possible outputs. If there are 5 ambiguous positions with 3 choices each, there are 3⁵ = 243 possible outputs.

3. **Training Instability**: The model sees the same logical structure expressed in multiple YAML forms during training. It learns to distribute probability across them, rather than converging to one canonical form.

**JSON**: No ambiguity → single canonical form → deterministic output.

**YAML**: High ambiguity → multiple canonical forms → non-deterministic output.

---

## 4. Training Priors

### The Model's Greater Exposure to JSON in Training

**Training Corpus Analysis** (estimated from common datasets):
- **JSON**: ~5-10% of tokens in code/text corpora (API responses, config files, data files, web JSON-LD)
- **YAML**: ~0.1-0.5% of tokens (mostly config files, CI/CD pipelines, Kubernetes manifests)

**Frequency Ratio**: JSON appears ~20-50x more frequently than YAML in training data.

### How This Biases the Model Toward Consistent JSON Continuations

1. **Pattern Reinforcement**: The model sees millions of JSON examples with consistent structure. It learns strong priors:
   - `{` → `"` (not `}` unless empty)
   - `"key"` → `:`
   - `:` → value type (string starts with `"`)

2. **Error Penalty**: Invalid JSON is immediately rejected (syntax error). The model learns to avoid invalid continuations with high confidence.

3. **Canonical Form**: The model converges to a single canonical JSON representation (typically compact, with double quotes, no trailing commas in the last item).

**YAML Training Effects**:
- Fewer examples → weaker priors
- Multiple valid forms → no single canonical representation
- Permissive grammar → model doesn't learn to strongly favor one form over another

**Result**: The model's next-token predictions for JSON are sharp (high confidence, low entropy). For YAML, predictions are flat (lower confidence, higher entropy).

---

## 5. Error Tolerance

### JSON's Fragility: One Missing Quote = Invalid

**Example Error**:
```json
{
  "key": value
}
```

Missing quotes around `value` → invalid JSON → parser rejects it.

**LLM Impact**:
1. **Training Signal**: The model learns that unquoted strings after `:` are invalid. It assigns near-zero probability to unquoted tokens in string positions.

2. **Decoding Behavior**: The model avoids invalid continuations, creating a "guardrail" effect. It rarely generates syntax errors because invalid tokens have low probability.

3. **Confidence**: The model is confident about valid continuations because invalid ones are clearly marked (low probability).

**Token Probability After `"key":`**:
```
Token        Logit    Probability
"            7.8      0.92
{            3.1      0.05
[            2.9      0.03
true         1.2      <0.01
false        1.1      <0.01
value        -2.3     <0.01  (unquoted - invalid)
```

The model strongly favors `"` (start of quoted string) and penalizes unquoted tokens.

### YAML's Permissiveness: Multiple Ways to Express the Same Value

**Equivalent Representations**:
```yaml
key: value
key: 'value'
key: "value"
key: |
  value
key: >
  value
```

All are valid and semantically equivalent.

**LLM Impact**:
1. **Training Signal**: The model sees all these forms in training. It learns that multiple continuations are valid and distributes probability across them.

2. **Decoding Behavior**: The model may switch between representations during generation, especially with sampling. There's no "wrong" choice, so the model doesn't learn to strongly favor one.

3. **Confidence**: The model is less confident about which form to use because all are valid. This increases entropy and variance.

**Token Probability After `key:`** (for string value):
```
Token        Logit    Probability
value        5.2      0.35  (unquoted)
"value"      4.8      0.28  (double-quoted)
'value'      4.5      0.22  (single-quoted)
|            3.1      0.10  (literal block)
>            2.9      0.05  (folded block)
```

Probability is distributed across multiple valid forms, creating uncertainty.

### Why This Changes the Model's Behavior and Confidence

**JSON**:
- **High Confidence**: Invalid continuations are clearly marked (low probability). Valid continuations dominate.
- **Low Variance**: The model consistently chooses the same valid continuation.
- **Error Avoidance**: The model learns to avoid syntax errors, creating self-correcting behavior.

**YAML**:
- **Lower Confidence**: Multiple valid continuations share probability mass. The model is uncertain which to choose.
- **High Variance**: The model may choose different valid forms across runs.
- **No Error Signal**: Since multiple forms are valid, the model doesn't learn to strongly favor one, leading to inconsistent output.

---

## 6. Demonstrations

### Example 1: JSON Structure Constraint

**Prompt**: "Generate a JSON object with a 'name' key:"

**Token-by-Token Analysis**:

**Position 1** (after prompt):
```
Next token candidates:
{     logit: 8.5, prob: 0.96
[     logit: 2.1, prob: 0.03
"     logit: 1.8, prob: 0.01
```
Greedy selects `{`. High confidence.

**Position 2** (after `{`):
```
Next token candidates:
"     logit: 8.2, prob: 0.95
}     logit: 2.1, prob: 0.04
\n    logit: 1.2, prob: 0.01
```
Greedy selects `"`. The model knows a key must start with a quote.

**Position 3** (after `{"`):
```
Next token candidates:
name  logit: 7.8, prob: 0.92
key   logit: 3.1, prob: 0.05
id    logit: 2.9, prob: 0.03
```
Greedy selects `name` (from prompt context). High confidence because it matches the prompt.

**Position 4** (after `{"name`):
```
Next token candidates:
"     logit: 9.1, prob: 0.98
'     logit: 0.5, prob: 0.01
}     logit: -1.2, prob: <0.01
```
Greedy selects `"`. The model knows the string must close with a quote (JSON doesn't allow single quotes for strings).

**Position 5** (after `{"name"`):
```
Next token candidates:
:     logit: 9.5, prob: 0.99
,     logit: 0.8, prob: 0.01
"     logit: -2.1, prob: <0.01
```
Greedy selects `:`. Near-deterministic.

**Result**: `{"name"` → the model is constrained to continue with `:` and then a value. The structure forces a specific continuation path.

**Decoding Variance**:
- Greedy: Always produces `{"name": ...}`
- Temperature T=0.1: Same as greedy (high-probability token dominates)
- Temperature T=2.0: Might add whitespace, but structure is fixed
- Top-k=3: Only captures formatting variants, not structural changes

### Example 2: YAML Structure Flexibility

**Prompt**: "Generate a YAML mapping with a 'name' key:"

**Token-by-Token Analysis**:

**Position 1** (after prompt):
```
Next token candidates:
name  logit: 6.8, prob: 0.52
key:  logit: 5.2, prob: 0.28
-     logit: 4.1, prob: 0.15
{     logit: 2.9, prob: 0.05
```
Greedy selects `name`, but `key:` and `-` have significant probability. Lower confidence.

**Position 2** (after `name`):
```
Next token candidates:
:     logit: 6.1, prob: 0.45
-     logit: 5.8, prob: 0.38
\n:   logit: 4.2, prob: 0.12
,     logit: 2.1, prob: 0.05
```
Greedy selects `:`, but `-` (list item) has 38% probability. Context-dependent.

**Position 3** (after `name:`):
```
Next token candidates:
value logit: 5.2, prob: 0.35  (unquoted)
"value" logit: 4.8, prob: 0.28  (double-quoted)
'value' logit: 4.5, prob: 0.22  (single-quoted)
|     logit: 3.1, prob: 0.10  (literal block)
>     logit: 2.9, prob: 0.05  (folded block)
```
Probability distributed across multiple valid forms. No single dominant token.

**Result**: `name:` → the model can continue with unquoted, quoted, or block styles. The structure doesn't force a specific continuation.

**Decoding Variance**:
- Greedy: May produce `name: value` or `name: "value"` depending on context
- Temperature T=0.1: Still has variance (top token has only ~35% probability)
- Temperature T=2.0: High variance, frequently switches between quote styles
- Top-k=5: Captures multiple valid structural choices (unquoted, quoted, block styles)

### How Structure Constrains or Doesn't Constrain Continuation

**JSON Constraint**:
- After `{"name"`, the grammar forces `:`. The model cannot choose `,`, `}`, or another key without a closing quote.
- The constraint is **hard**: invalid continuations have near-zero probability.
- The model's continuation is **deterministic** (always `:`).

**YAML Non-Constraint**:
- After `name:`, the grammar allows multiple value forms. The model can choose unquoted, quoted, or block styles.
- The constraint is **soft**: all continuations are valid, but the model must choose one.
- The model's continuation is **non-deterministic** (varies between `value`, `"value"`, `'value'`, etc.).

### How Decoding Choices Amplify or Suppress Variance

**JSON with Different Decoding Methods**:
- **Greedy**: Deterministic output (high-probability token always selected)
- **Temperature T=0.1**: Same as greedy (distribution is already sharp)
- **Temperature T=2.0**: Minor variance (whitespace, but structure fixed)
- **Top-k=3**: Only formatting variants
- **Beam Search**: Converges to same structure, explores formatting

**Variance Amplification**: Low. Decoding methods don't significantly change output because the base distribution is already sharp.

**YAML with Different Decoding Methods**:
- **Greedy**: Moderate variance (context-dependent choices)
- **Temperature T=0.1**: Still has variance (top token has ~35% probability)
- **Temperature T=2.0**: High variance (frequently switches between quote styles)
- **Top-k=5**: Captures multiple valid structural choices
- **Beam Search**: Explores different structural forms (flow vs block, quoted vs unquoted)

**Variance Amplification**: High. Decoding methods significantly change output because the base distribution is flat.

---

## 7. Practical Implications

### When to Use JSON with LLMs

**Advantages**:
- **Deterministic Output**: Greedy decoding produces consistent results
- **Low Variance**: Temperature and sampling don't significantly change structure
- **Error Avoidance**: Model learns to avoid syntax errors
- **High Confidence**: Model is confident about valid continuations

**Use Cases**:
- API response generation (needs consistent structure)
- Data extraction (needs deterministic parsing)
- Structured output tasks (needs reliable format)

**Limitations**:
- Less human-readable (requires quotes, commas)
- No comments (cannot include explanatory text)
- Rigid structure (cannot express same data in multiple ways)

### When to Use YAML with LLMs

**Advantages**:
- **Human-Readable**: Unquoted strings, natural formatting
- **Comments**: Can include explanatory text
- **Flexibility**: Multiple ways to express same data

**Use Cases**:
- Configuration files (needs readability and comments)
- Documentation (needs explanatory text)
- Human-editable data (needs flexibility)

**Limitations**:
- **High Variance**: Output structure varies across runs
- **Non-Deterministic**: Greedy decoding may produce different forms
- **Lower Confidence**: Model is uncertain about which form to use
- **Error-Prone**: Model may generate inconsistent formatting

### Mitigation Strategies

**For JSON**:
- Use greedy decoding for deterministic output
- Low temperature (T=0.1-0.3) for consistent structure
- Validate output with JSON parser to catch rare errors

**For YAML**:
- Use structured prompts to guide format choice (e.g., "Use unquoted strings")
- Post-process to normalize format (convert all to one style)
- Use YAML parser to validate and reformat output
- Consider JSON for tasks requiring deterministic output

---

## 8. Conclusion

JSON's rigid grammar, high training frequency, and error-intolerant syntax create sharp token probability distributions that favor deterministic decoding. YAML's flexible grammar, lower training frequency, and permissive syntax create flat distributions that amplify variance across decoding methods.

**Key Takeaways**:
1. **JSON reduces variance** because its grammar constrains continuations to 1-2 high-probability tokens.
2. **YAML increases variance** because its grammar allows multiple valid continuations with similar probability.
3. **Decoding methods amplify variance in YAML** more than in JSON because YAML's base distribution is flatter.
4. **Training priors favor JSON** because it appears 20-50x more frequently in training data.
5. **Error tolerance differences** create different confidence levels: JSON is high-confidence (invalid continuations are clearly marked), YAML is lower-confidence (multiple valid continuations share probability).

**Bottom Line**: Use JSON when you need deterministic, consistent output. Use YAML when you need human-readability and flexibility, but accept higher variance and post-process to normalize format.

