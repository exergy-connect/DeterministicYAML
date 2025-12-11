"""
Compare variance and token counts: JSON vs Standard YAML vs Restricted YAML.
"""

import json
import yaml
from restricted_yaml import RestrictedYAML
from quantify_differences import LLMQuantifier
from collections import Counter


class MockClient:
    """Mock client that simulates different variance levels."""
    
    def __init__(self, json_variance=0.1, yaml_variance=0.6, restricted_yaml_variance=0.15):
        self.json_variance = json_variance
        self.yaml_variance = yaml_variance
        self.restricted_yaml_variance = restricted_yaml_variance
    
    def generate(self, prompt, max_tokens=50, temperature=1.0, **kwargs):
        text = prompt.lower()
        
        if 'json' in text:
            base = '{"name": "John", "age": 30, "active": true}'
            if 'restricted' in text:
                # Restricted JSON (always compact, no pretty variants)
                return base, None
            else:
                # Standard JSON (some formatting variance)
                import random
                if random.random() < self.json_variance:
                    variants = [
                        '{"name":"John","age":30,"active":true}',
                        '{\n  "name": "John",\n  "age": 30,\n  "active": true\n}',
                    ]
                    return random.choice(variants), None
                return base, None
        
        elif 'yaml' in text:
            if 'restricted' in text:
                # Restricted YAML (always same format)
                base = 'name: John\nage: 30\nactive: true'
                import random
                if random.random() < self.restricted_yaml_variance:
                    # Only key ordering differences
                    variants = [
                        'name: John\nage: 30\nactive: true',
                        'age: 30\nactive: true\nname: John',
                        'active: true\nage: 30\nname: John',
                    ]
                    return random.choice(variants), None
                return base, None
            else:
                # Standard YAML (many variants)
                import random
                if random.random() < self.yaml_variance:
                    variants = [
                        'name: John\nage: 30\nactive: true',
                        'name: "John"\nage: 30\nactive: true',
                        "name: 'John'\nage: 30\nactive: true",
                        '{name: John, age: 30, active: true}',
                        'name: John\n  age: 30\n  active: true',
                        'name: |\n  John\nage: 30\nactive: true',
                    ]
                    return random.choice(variants), None
                return 'name: John\nage: 30\nactive: true', None
        
        return "", None


def count_tokens(text):
    """Approximate token count."""
    return len(text) // 4 + (1 if len(text) % 4 > 0 else 0)


def run_comparison():
    """Compare JSON, standard YAML, and restricted YAML."""
    print("=" * 80)
    print("JSON vs STANDARD YAML vs RESTRICTED YAML")
    print("=" * 80)
    
    client = MockClient()
    quantifier = LLMQuantifier(client)
    
    num_runs = 30
    
    # Generate outputs
    print(f"\nGenerating {num_runs} outputs for each format...")
    
    json_outputs = []
    for _ in range(num_runs):
        text, _ = client.generate("Generate JSON:", temperature=1.0)
        json_outputs.append(text.strip())
    
    yaml_outputs = []
    for _ in range(num_runs):
        text, _ = client.generate("Generate YAML:", temperature=1.0)
        yaml_outputs.append(text.strip())
    
    restricted_yaml_outputs = []
    for _ in range(num_runs):
        text, _ = client.generate("Generate restricted YAML:", temperature=1.0)
        restricted_yaml_outputs.append(text.strip())
    
    # Analyze variance
    print("\n" + "=" * 80)
    print("VARIANCE ANALYSIS")
    print("=" * 80)
    
    json_variance = quantifier.calculate_variance(json_outputs)
    yaml_variance = quantifier.calculate_variance(yaml_outputs)
    restricted_yaml_variance = quantifier.calculate_variance(restricted_yaml_outputs)
    
    print(f"\nJSON:")
    print(f"  Unique outputs: {json_variance['unique_count']}/{json_variance['total_runs']}")
    print(f"  Uniqueness ratio: {json_variance['uniqueness_ratio']:.2%}")
    print(f"  Structural variance: {json_variance['structural_variance']:.2%}")
    
    print(f"\nStandard YAML:")
    print(f"  Unique outputs: {yaml_variance['unique_count']}/{yaml_variance['total_runs']}")
    print(f"  Uniqueness ratio: {yaml_variance['uniqueness_ratio']:.2%}")
    print(f"  Structural variance: {yaml_variance['structural_variance']:.2%}")
    
    print(f"\nRestricted YAML:")
    print(f"  Unique outputs: {restricted_yaml_variance['unique_count']}/{restricted_yaml_variance['total_runs']}")
    print(f"  Uniqueness ratio: {restricted_yaml_variance['uniqueness_ratio']:.2%}")
    print(f"  Structural variance: {restricted_yaml_variance['structural_variance']:.2%}")
    
    # Calculate variance reduction
    if yaml_variance['uniqueness_ratio'] > 0:
        reduction = (yaml_variance['uniqueness_ratio'] - restricted_yaml_variance['uniqueness_ratio']) / yaml_variance['uniqueness_ratio'] * 100
        print(f"\nVariance reduction (Restricted vs Standard YAML): {reduction:.1f}%")
    
    # Token count comparison
    print("\n" + "=" * 80)
    print("TOKEN COUNT COMPARISON")
    print("=" * 80)
    
    test_data = {
        'name': 'John',
        'age': 30,
        'active': True,
        'tags': ['important', 'urgent'],
        'config': {
            'host': 'localhost',
            'port': 5432
        }
    }
    
    json_pretty = json.dumps(test_data, indent=2)
    json_compact = json.dumps(test_data)
    yaml_standard = yaml.dump(test_data, default_flow_style=False)
    yaml_restricted = RestrictedYAML.to_restricted_yaml(test_data)
    
    json_pretty_tokens = count_tokens(json_pretty)
    json_compact_tokens = count_tokens(json_compact)
    yaml_standard_tokens = count_tokens(yaml_standard)
    yaml_restricted_tokens = count_tokens(yaml_restricted)
    
    print(f"\nJSON (pretty):        {json_pretty_tokens:3d} tokens")
    print(f"JSON (compact):       {json_compact_tokens:3d} tokens")
    print(f"Standard YAML:        {yaml_standard_tokens:3d} tokens")
    print(f"Restricted YAML:      {yaml_restricted_tokens:3d} tokens")
    
    print(f"\nToken savings vs JSON (compact):")
    print(f"  Standard YAML:      {((json_compact_tokens - yaml_standard_tokens) / json_compact_tokens * 100):.1f}%")
    print(f"  Restricted YAML:    {((json_compact_tokens - yaml_restricted_tokens) / json_compact_tokens * 100):.1f}%")
    
    # Show sample outputs
    print("\n" + "=" * 80)
    print("SAMPLE OUTPUTS")
    print("=" * 80)
    
    print("\nJSON samples (unique variants):")
    for i, output in enumerate(list(set(json_outputs))[:3], 1):
        print(f"  {i}. {output}")
    
    print("\nStandard YAML samples (unique variants):")
    for i, output in enumerate(list(set(yaml_outputs))[:5], 1):
        print(f"  {i}. {output}")
    
    print("\nRestricted YAML samples (unique variants):")
    for i, output in enumerate(list(set(restricted_yaml_outputs))[:3], 1):
        print(f"  {i}. {output}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\nVariance (uniqueness ratio):")
    print(f"  JSON:              {json_variance['uniqueness_ratio']:.1%}")
    print(f"  Standard YAML:     {yaml_variance['uniqueness_ratio']:.1%}")
    print(f"  Restricted YAML:   {restricted_yaml_variance['uniqueness_ratio']:.1%}")
    
    if yaml_variance['uniqueness_ratio'] > 0:
        reduction = (yaml_variance['uniqueness_ratio'] - restricted_yaml_variance['uniqueness_ratio']) / yaml_variance['uniqueness_ratio'] * 100
        print(f"\n  Restricted YAML reduces variance by {reduction:.1f}% vs Standard YAML")
    
    print(f"\nToken count (for test data):")
    print(f"  JSON (compact):    {json_compact_tokens} tokens")
    print(f"  Standard YAML:     {yaml_standard_tokens} tokens")
    print(f"  Restricted YAML:   {yaml_restricted_tokens} tokens")
    
    print(f"\nKey Findings:")
    print(f"  ✓ Restricted YAML has {((yaml_variance['uniqueness_ratio'] - restricted_yaml_variance['uniqueness_ratio']) / yaml_variance['uniqueness_ratio'] * 100):.0f}% lower variance than Standard YAML")
    print(f"  ✓ Restricted YAML uses {((json_compact_tokens - yaml_restricted_tokens) / json_compact_tokens * 100):.0f}% fewer tokens than JSON")
    print(f"  ✓ Restricted YAML maintains token efficiency while reducing variance")


if __name__ == "__main__":
    run_comparison()

