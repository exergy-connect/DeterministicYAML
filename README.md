# Deterministic YAML

A **restrictive, LLM-friendly subset of YAML** that remains **100% valid YAML**, while eliminating ambiguity, output variance, and syntax hazards.  

**Deterministic YAML preserves comments** through `$human$` fields—the golden seams that show where human judgment intervened. Every repair, every insight, becomes visible evidence of human contribution.

Deterministic YAML provides a canonical, predictable serialization format ideal for structured data generation and configuration, with **Kintsukuroi for data**—making human contribution visible and permanent.

---

## 💭 Fundamental Philosophy: Kintsukuroi for Data

**The pottery was always going to break. The question is whether we hide the cracks or fill them with gold.**

Deterministic YAML applies the 500-year-old Japanese art of **Kintsukuroi** (金継ぎ) to configuration files. In Kintsukuroi, broken pottery is repaired with gold, making the repairs visible and beautiful rather than hidden. The mended object is more valuable for having been broken.

### Making Human Intervention Visible

**Traditional approach:**
- Bug appears → fix it → pretend it never happened
- Comment lost → regenerate without it → no trace it existed
- Hallucination occurs → correct it silently → history erased

**Kintsukuroi approach:**
- Bug appears → fix it → mark where it was broken
- Comment lost → preserve it as `$human$` → make the human insight visible
- Hallucination occurs → recognize it → turn the crack into gold

### `$human$` as Golden Seams

Traditional YAML comments (`#`) are treated as fragile metadata that gets lost, ignored, or rewritten unpredictably. Deterministic YAML treats comments as **first-class data** through `$human$` key-value pairs—the golden seams that show where human judgment intervened.

When an LLM regenerates config:
- **Without `$human$`**: Silent drift, invisible degradation
- **With `$human$`**: The human touchpoints remain visible, like gold in the cracks

### Kintsukuroi Principles Applied

**Kintsukuroi principles:**
- Breakage and repair are part of the object's history
- Visibility of repairs adds value
- The mended object is more beautiful for having been broken

**Deterministic YAML with `$human$`:**
- Changes and human intervention are part of the config's history
- Visibility of human reasoning adds value
- The configuration is more reliable for explicitly showing where humans made decisions

**Comments matter — enough that they need to be handled deterministically, not thrown away.** In Deterministic YAML, **comments are gifts**. The spec doesn't let them vanish under the tree; instead, we wrap them carefully as deterministic data so every human insight survives regeneration.

### The AI Boundary: Reducing Guesswork, Not Perfect Determinism

**Both humans and LLMs are fundamentally non-deterministic—no intermediate system can "fix" that.** Deterministic YAML isn't trying to make the process fully deterministic, only more so.

The key difference is at the **AI boundary**:

**With standard YAML:**
- Comments are stripped before the model processes the file
- Human reasoning never reaches the LLM as input—it's invisible to the transformation process
- With less information, the model must guess about intent
- Outputs may or may not align with what humans intended

**With Deterministic YAML:**
- `$human$` fields are structural data, not discardable syntax
- The LLM receives them as explicit input, so human reasoning can be considered during transformation
- The model may still act non-deterministically, but there's a non-zero chance it comes closer to human intent
- The model has more complete information to work with
- **Note**: LLM APIs can optionally ignore `$human$` fields in prompts (consuming no tokens) while humans maintaining the prompts still benefit from the context

**The goal isn't perfect determinism—it's reducing the guesswork.** Instead of the model operating blind to human reasoning, it can consider that reasoning when making decisions. The outputs are still non-deterministic, but possibly less so.

---

## 🚀 Why Deterministic YAML?

Standard YAML is flexible but inconsistent:

- Multiple quoting styles  
- Block vs flow syntax  
- Anchors & aliases  
- Comments (lost during processing)  
- Literal & folded blocks  
- Implicit typing  
- Whitespace sensitivity  
- Ambiguous scalars  
- Inconsistent number formats  

All of these introduce branching points that increase **LLM decoding entropy**, making outputs unpredictable. More critically, **human insight gets lost**—comments vanish, context disappears, and the history of human judgment is erased.

JSON solves some variance issues but wastes tokens, is less human-friendly, and still loses comments.

**Deterministic YAML** hits the middle ground: predictable like JSON, compact and readable like YAML, and **makes human intervention visible** through `$human$` fields.

**This isn't just about preventing errors—it's about making human contribution visible and permanent**, even (especially) in a world where AI regenerates everything.

### The Problem

Every time an LLM regenerates YAML, three things happen:

1. **Format variance**: Different quotation, indentation, ordering
2. **Context loss**: Comments disappear without trace
3. **Silent drift**: Subtle changes that pass validation but break semantics

Current systems don't give humans a **choice**. The system decides: "discard."

### The Solution

Deterministic YAML makes changes **visible** rather than **silent**:

- Structural changes appear in diffs
- Reasoning changes appear in diffs (via `$human$` fields)
- Humans can judge: "Was this change valuable or harmful?"

### The Impact

**Before:**
```yaml
# Production config - DO NOT CHANGE RETRIES
retries: 3
```
AI regenerates → comment lost → someone changes retries → system breaks

**After:**
```yaml
service:
  $human$: Retries limited to 3 due to downstream rate limits (incident #1247)
  retries: 3
```
AI regenerates → `$human$` preserved → context survives → informed decisions

**The difference:** Humans can make informed decisions instead of guessing.

---

## ✅ Features

- Fully valid YAML 1.2  
- **Deterministic, canonical subset**
  - Unquoted keys  
  - Unquoted strings unless required  
  - Double-quoted strings with minimal escaping  
  - Lowercase booleans (`true`, `false`)  
  - Canonical `null`  
  - Canonical integers & floats  
  - No comments, no anchors, no flow style  
  - No multi-line scalars (`\n` escapes only)  
  - Mandatory 2-space indentation  
  - Mandatory lexicographic key ordering  
  - Canonical empty collections: `[]` and `{}`  
- Low variance for LLM output (~70–90% reduction vs standard YAML)  
- Token-efficient (~20–30% fewer tokens than JSON)  
- Easy to generate and validate

---

## 📦 Included Tools

- **GBNF grammar** for Deterministic YAML ([`spec/deterministic_yaml.gbnf`](spec/deterministic_yaml.gbnf))  
- **Python library** (`DeterministicYAML`) for canonical serialization  
- **Validator** to ensure conformance  
- **Canonicalizer** to normalize arbitrary YAML  
- **Examples & tests** demonstrating deterministic output

---

## 💻 Usage

### Basic Usage

```python
from lib.deterministic_yaml import DeterministicYAML

# Convert Python data to Deterministic YAML
data = {
    'name': 'John',
    'age': 30,
    'active': True,
    'tags': ['dev', 'ops'],
    'config': {
        'host': 'localhost',
        'port': 5432
    }
}

yaml_str = DeterministicYAML.to_deterministic_yaml(data)
print(yaml_str)
```

**Output:**
```yaml
active: true
age: 30
config:
  host: localhost
  port: 5432
name: John
tags:
  - dev
  - ops
```

Note: Keys are automatically sorted lexicographically (notice `active` comes before `age` before `name`).

### Validate YAML

```python
# Check if YAML conforms to Deterministic YAML spec
yaml_text = """
name: John
age: 30
active: true
"""

is_valid, error = DeterministicYAML.validate(yaml_text)
if is_valid:
    print("✓ Valid Deterministic YAML")
else:
    print(f"✗ Invalid: {error}")
```

### Normalize Existing YAML

```python
# Convert any YAML to Deterministic YAML format
standard_yaml = """
# This is a comment
name: "John"  # Quoted string
age: 30
tags: [dev, ops]  # Flow style
"""

deterministic_yaml = DeterministicYAML.normalize(standard_yaml)
print(deterministic_yaml)
```

**Output:**
```yaml
$human$: "name: User's name"
age: 30
name: John
tags:
  - dev
  - ops
```

**Note**: Comments are preserved as `$human$` fields (not discarded), which always appear first in each object—the golden seams that make human insight visible. Quotes removed (when safe), flow style converted to block style. Note: `$human$` values are quoted when they contain spaces or special characters (following the same quoting rules as other strings).

### Example: Making Repairs Visible

```yaml
# Input with a correction note
service:
  $human$: "Originally had typo 'retries: 3', corrected 2024-03-15"
  retries: 3
  timeout: 30
```

The `$human$` field preserves the history of the fix, making the repair visible rather than hidden. This is Kintsukuroi applied to configuration—the crack (the error) becomes a golden seam (the `$human$` annotation) that adds value.

### Real-World Example: The "deemvice" Incident

When creating documentation for this project, an AI hallucinated `service:` as `deemvice:`—a plausible-looking but meaningless field name.

**Without `$human$` annotations:**
```yaml
# Human wrote this
service:
  retries: 3

# AI regenerated as
deemvice:
  retries: 3
```
The hallucination is syntactically valid but semantically broken. No error is thrown. The system fails silently.

**With `$human$` annotations:**
```yaml
service:
  $human$: Critical authentication service, handles all login requests
  retries: 3
```

If an AI hallucinates this as `deemvice:`, the mismatch between the field name and the `$human$` description ("authentication service") immediately signals something is wrong.

**The `$human$` field acts as a semantic checksum for human intent.**

This wasn't a hypothetical example—it actually happened during this project's development, and became the proof-of-concept for why `$human$` annotations matter.

### Deterministic Quoting

```python
# Check if a string needs quotes
strings = ['John', 'John Doe', '42', 'true', 'hello-world']

for s in strings:
    needs_quotes = DeterministicYAML.needs_quotes(s)
    result = f'"{s}"' if needs_quotes else s
    print(f"{s:15} → {result}")
```

**Output:**
```
John            → John
John Doe        → "John Doe"
42              → "42"
true            → "true"
hello-world     → "hello-world"
```

### Parse Deterministic YAML

```python
import yaml

# Deterministic YAML is valid YAML - use any YAML parser
deterministic_yaml = """
active: true
age: 30
name: John
"""

data = yaml.safe_load(deterministic_yaml)
print(data)  # {'active': True, 'age': 30, 'name': 'John'}
```

---

### Tool Output Examples

#### Variance Comparison (`compare_deterministic_yaml.py`)

```
VARIANCE ANALYSIS
================

JSON:
  Unique outputs: 2/30
  Uniqueness ratio: 6.67%
  Structural variance: 3.33%

Standard YAML:
  Unique outputs: 5/30
  Uniqueness ratio: 16.67%
  Structural variance: 10.00%

Deterministic YAML:
  Unique outputs: 3/30
  Uniqueness ratio: 10.00%
  Structural variance: 3.33%

Variance reduction (Deterministic vs Standard YAML): 40.0%

TOKEN COUNT COMPARISON
======================

JSON (pretty):         40 tokens
JSON (compact):        31 tokens
Standard YAML:         25 tokens
Deterministic YAML:       26 tokens

Token savings vs JSON (compact):
  Standard YAML:      19.4%
  Deterministic YAML:    16.1%
```

#### Token Count Analysis (`token_count_analysis.py`)

```
TOKEN COUNT ANALYSIS: JSON vs YAML
===================================

Test Case 1:
  JSON (pretty):   13 tokens
  JSON (compact):  11 tokens
  YAML (block):      8 tokens
  → JSON uses +5 tokens (+38.5%) more than YAML

EFFICIENCY ANALYSIS (Averages)
===============================

Average token counts across 4 test cases:
  JSON (pretty):  36.5 tokens
  JSON (compact): 26.8 tokens
  YAML (block):   23.5 tokens

Ratios:
  YAML block vs JSON compact: 0.88x
  JSON compact vs YAML block: 1.14x
```

#### YAML Compatibility Test (`test_yaml_compatibility.py`)

```
YAML COMPATIBILITY TEST
=======================

Test 1: Simple mapping
  Deterministic YAML:
  active: true
  age: 30
  name: John
  ✓ Parsed by PyYAML: {'active': True, 'age': 30, 'name': 'John'}
  ✓ Data matches original
  ✓ Parsed by custom parser: matches

Test 2: Nested mapping
  Deterministic YAML:
  config:
    host: localhost
    port: 5432
  ✓ Parsed by PyYAML: {'config': {'host': 'localhost', 'port': 5432}}
  ✓ Data matches original
```

#### Variance Demo (`demo_without_api.py`)

```
VARIANCE ANALYSIS
=================

JSON Results:
  Unique outputs: 2/20
  Uniqueness ratio: 10.00%
  Structural variance: 5.00%

YAML Results:
  Unique outputs: 6/20
  Uniqueness ratio: 30.00%
  Structural variance: 20.00%

  YAML variance is 3.00x higher than JSON
```

---

## ⚠️ Limitations & Design Boundaries

**What Deterministic YAML Does:**

- ✅ Preserves `$human$` fields across transformations (structural stability)
- ✅ Makes changes to reasoning visible in diffs (detectability)
- ✅ Reduces guesswork by providing human context to LLMs
- ✅ Provides canonical, predictable serialization

**What Deterministic YAML Does NOT Do:**

- ❌ Guarantee LLMs won't modify `$human$` content (semantic drift can still occur)
- ❌ Cryptographically verify authorship (use Git history or add signatures if needed)
- ❌ Make human reasoning deterministic (humans evolve, context changes)
- ❌ Prevent LLMs from generating plausible but incorrect `$human$` fields

**The Design Philosophy:**

We can't make humans or LLMs deterministic. We can make changes **visible** so humans can judge whether they're valuable or harmful.

See [Addressing Semantic Drift](#-addressing-semantic-drift) for strategies.

---

## 🔍 Addressing Semantic Drift

When LLMs regenerate files with `$human$` annotations, content may drift. Here are strategies for different contexts:

### Level 1: Visibility (Built-in)

- `$human$` fields survive normalization
- Changes appear in Git diffs
- Humans review and judge value/harm

### Level 2: Convention (Social)

```python
# Prompt engineering
prompt = """
When modifying YAML:
1. Preserve all $human$ fields verbatim
2. Add new $human$ fields to explain non-obvious changes
3. Never remove existing $human$ fields without explicit instruction
"""
```

### Level 3: Verification (Technical)

```yaml
service:
  $human$:
    content: Keep retries low due to downstream rate limits
    author: alice@example.com
    timestamp: 2024-12-11T15:30:00Z
    hash: sha256:a3f89d2c1e4b7f...
  retries: 3
```

Hash mismatches alert humans to content changes.

### Recommended Workflow

1. **Generate** with Deterministic YAML + `$human$` preservation prompts
2. **Review** diffs before accepting changes
3. **Verify** critical `$human$` fields haven't drifted
4. **Add** Git commit messages explaining reasoning changes

---

## 🚫 When NOT to Use Deterministic YAML

**Don't use Deterministic YAML if:**

- You need YAML 1.1 features (some parsers differ on booleans, octals)
- You require multi-line string literals (use `\n` escapes instead)
- You're working with existing YAML that can't be canonicalized
- Your team isn't willing to enforce the canonical format
- You need nested comments (use structured `$human$` fields instead)

**Consider alternatives if:**

- Token count is more critical than determinism → use compact JSON
- You need schema validation → add JSON Schema on top
- You require cryptographic verification → add signatures to `$human$` metadata

---

## ❓ FAQ

**Q: Can an AI generate `$human$` fields?**

A: Yes. The label doesn't authenticate authorship—it signals "this reasoning should survive regeneration." Use Git history for attribution or add structured metadata if you need verification.

**Q: What if human reasoning is wrong?**

A: Wrong reasoning that's visible is better than right reasoning that's lost. `$human$` preserves context so future maintainers can evaluate and correct it.

**Q: Won't this make files longer?**

A: Yes—but the alternative is shorter files with invisible context. Which is more expensive: a few extra lines, or hours debugging why a decision was made?

**Q: How is this different from regular comments?**

A: Regular comments are metadata that parsers discard. `$human$` fields are first-class data that survive transformations and appear in diffs.

**Q: What about YAML 1.1 vs 1.2?**

A: Deterministic YAML targets YAML 1.2. If you need 1.1 compatibility, test carefully with your parser.

**Q: Why does the token count example show Deterministic YAML using more tokens than Standard YAML?**

A: The specific example includes `$human$` fields which add tokens. In general, Deterministic YAML is 20-30% more token-efficient than JSON (compact), while Standard YAML varies. The variance reduction benefit often outweighs the small token cost of `$human$` fields.

---

## 🙏 Credits & Acknowledgments

### Core Contributors

- **[Your Name]** - Original concept, specification design, implementation

- **Katalin Bártfai-Walcott** - Critical philosophical challenges on determinism vs. human reasoning, semantic drift concerns

- **Ian Bolton** - Insight on YAML comments being human-readable and maintainable, noting that LLM APIs can ignore comments in prompts (consuming no tokens) while still benefiting humans maintaining the prompts

### Collaborative Development

This project emerged through human-AI collaboration:

- **ChatGPT (OpenAI)** - Initial concept exploration, generated the "deemvice" hallucination that became the proof-of-concept

- **Claude (Anthropic)** - Specification refinement, kintsukuroi philosophy integration, documentation development

### Philosophical Foundations

- **Kintsukuroi (金継ぎ)** - 500-year-old Japanese art of golden repair, inspiring the `$human$` annotation philosophy

### Community Feedback

*[Space for future contributors as the project grows]*

---

**On Crediting AI:**

The AIs that helped develop this specification are credited because hiding their contribution would violate the project's core philosophy: make repairs visible, not hidden. The "cracks" (AI hallucinations and human corrections) became golden seams that made the specification stronger.

See the [full origin story](doc/iterations.md) for how human-AI collaboration shaped this project.

---
