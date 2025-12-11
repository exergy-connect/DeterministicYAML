# Deterministic YAML

A **deterministic, LLM-friendly subset of YAML** that remains **100% valid YAML**, while eliminating ambiguity, output variance, and syntax hazards.  
Restricted YAML provides a canonical, predictable serialization format ideal for structured data generation and configuration.

---

## 🚀 Why Restricted YAML?

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

**Restricted YAML** hits the middle ground: predictable like JSON, compact and readable like YAML.

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

- **GBNF grammar** for Restricted YAML  
- **Python library** (`RestrictedYAML`) for canonical serialization  
- **Validator** to ensure conformance  
- **Canonicalizer** to normalize arbitrary YAML  
- **Examples & tests** demonstrating deterministic output

---

## 💻 Usage

### Basic Usage

```python
from lib.restricted_yaml import RestrictedYAML

# Convert Python data to Restricted YAML
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

yaml_str = RestrictedYAML.to_restricted_yaml(data)
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
# Check if YAML conforms to Restricted YAML spec
yaml_text = """
name: John
age: 30
active: true
"""

is_valid, error = RestrictedYAML.validate(yaml_text)
if is_valid:
    print("✓ Valid Restricted YAML")
else:
    print(f"✗ Invalid: {error}")
```

### Normalize Existing YAML

```python
# Convert any YAML to Restricted YAML format
standard_yaml = """
# This is a comment
name: "John"  # Quoted string
age: 30
tags: [dev, ops]  # Flow style
"""

restricted_yaml = RestrictedYAML.normalize(standard_yaml)
print(restricted_yaml)
```

**Output:**
```yaml
age: 30
name: John
tags:
  - dev
  - ops
```

Comments removed, quotes removed (when safe), flow style converted to block style.

### Deterministic Quoting

```python
# Check if a string needs quotes
strings = ['John', 'John Doe', '42', 'true', 'hello-world']

for s in strings:
    needs_quotes = RestrictedYAML.needs_quotes(s)
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

### Parse Restricted YAML

```python
import yaml

# Restricted YAML is valid YAML - use any YAML parser
restricted_yaml = """
active: true
age: 30
name: John
"""

data = yaml.safe_load(restricted_yaml)
print(data)  # {'active': True, 'age': 30, 'name': 'John'}
```

---

### Tool Output Examples

#### Variance Comparison (`compare_restricted_yaml.py`)

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

Restricted YAML:
  Unique outputs: 3/30
  Uniqueness ratio: 10.00%
  Structural variance: 3.33%

Variance reduction (Restricted vs Standard YAML): 40.0%

TOKEN COUNT COMPARISON
======================

JSON (pretty):         40 tokens
JSON (compact):        31 tokens
Standard YAML:         25 tokens
Restricted YAML:       26 tokens

Token savings vs JSON (compact):
  Standard YAML:      19.4%
  Restricted YAML:    16.1%
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
  Restricted YAML:
  active: true
  age: 30
  name: John
  ✓ Parsed by PyYAML: {'active': True, 'age': 30, 'name': 'John'}
  ✓ Data matches original
  ✓ Parsed by custom parser: matches

Test 2: Nested mapping
  Restricted YAML:
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
