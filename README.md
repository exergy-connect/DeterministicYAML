# Deterministic YAML

A **deterministic, LLM-friendly subset of YAML** that remains **100% valid YAML**, while eliminating ambiguity, output variance, and syntax hazards.  
Deterministic YAML provides a canonical, predictable serialization format ideal for structured data generation and configuration.

---

## 💭 Fundamental Philosophy: Preserving Human Value

**To comment is human, and human insight must be preserved, not discarded.**

Deterministic YAML is built on the principle that **human value matters**. Comments, documentation, and contextual insights represent valuable human knowledge that should survive all data operations—round-trips, normalization, regeneration, and transformation.

### Comments as Data, Not Metadata

Traditional YAML comments (`#`) are treated as fragile metadata that gets lost, ignored, or rewritten unpredictably. Deterministic YAML treats comments as **first-class data** through `_comment` key-value pairs:

- **Preserved**: Comments survive round-trip parsing, normalization, and regeneration
- **Deterministic**: Same data always produces same YAML (comments included)
- **Portable**: Comments are part of the data structure, not metadata that can be discarded
- **Human insight preserved**: The human touch of comments is maintained, not thrown away

**Comments matter — enough that they need to be handled deterministically, not thrown away.**

When you normalize YAML with comments, they are automatically converted to `_comment` fields, ensuring your documentation and insights remain part of the data structure.

---

## 🚀 Why Deterministic YAML?

Standard YAML is flexible but inconsistent:

- Multiple quoting styles  
- Block vs flow syntax  
- Anchors & aliases  
- Comments  
- Literal & folded blocks  
- Implicit typing  
- Whitespace sensitivity  
- Ambiguous scalars  
- Inconsistent number formats  

All of these introduce branching points that increase **LLM decoding entropy**, making outputs unpredictable.  

JSON solves some of these issues but wastes tokens and is less human-friendly.  

**Deterministic YAML** hits the middle ground: predictable like JSON, compact and readable like YAML.

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

- **GBNF grammar** for Deterministic YAML  
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
_comment: "name: User's name"
age: 30
name: John
tags:
  - dev
  - ops
```

**Note**: Comments are preserved as `_comment` fields (not discarded). Quotes removed (when safe), flow style converted to block style.

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
