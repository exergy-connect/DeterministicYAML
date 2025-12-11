"""
Demo script that runs without API access to demonstrate quantification concepts.

This uses simulated outputs to show how the quantification metrics work.

Copyright (c) 2025 Exergy ∞ LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from quantify_differences import LLMQuantifier
import json
import yaml
import random


class MockClient:
    """Mock LLM client that generates simulated outputs."""
    
    def __init__(self, json_variance=0.1, yaml_variance=0.6):
        """
        Initialize with variance parameters.
        
        Args:
            json_variance: Probability of generating a variant JSON output
            yaml_variance: Probability of generating a variant YAML output
        """
        self.json_variance = json_variance
        self.yaml_variance = yaml_variance
    
    def generate(self, prompt, max_tokens=50, temperature=1.0, **kwargs):
        """Generate mock output based on prompt."""
        text = prompt.lower()
        
        # JSON outputs (low variance)
        if 'json' in text:
            base = '{"name": "John", "age": 30, "active": true}'
            
            # Low variance: mostly the same, occasional formatting differences
            if random.random() < self.json_variance:
                variants = [
                    '{"name":"John","age":30,"active":true}',  # No spaces
                    '{\n  "name": "John",\n  "age": 30,\n  "active": true\n}',  # Pretty
                    '{"active": true, "age": 30, "name": "John"}',  # Different order (normalized same)
                ]
                return random.choice(variants), None
            else:
                return base, None
        
        # YAML outputs (high variance)
        elif 'yaml' in text:
            # High variance: many different valid forms
            variants = [
                'name: John\nage: 30\nactive: true',
                'name: "John"\nage: 30\nactive: true',
                "name: 'John'\nage: 30\nactive: true",
                'name: John\n  age: 30\n  active: true',
                'name: |\n  John\nage: 30\nactive: true',
                '{name: John, age: 30, active: true}',  # Flow style
                'name: John\nage: 30\nactive: true\n# Comment',
            ]
            
            # Higher probability of variation
            if random.random() < self.yaml_variance:
                return random.choice(variants), None
            else:
                return variants[0], None
        
        return "", None


def run_demo():
    """Run demonstration with mock client."""
    print("=" * 80)
    print("JSON vs YAML Quantification Demo (Mock Data)")
    print("=" * 80)
    print("\nThis demo uses simulated outputs to demonstrate the quantification metrics.")
    print("In practice, use run_quantification.py with a real API client.\n")
    
    # Create mock client with realistic variance
    client = MockClient(json_variance=0.15, yaml_variance=0.70)
    quantifier = LLMQuantifier(client)
    
    # Generate outputs
    num_runs = 20
    
    print(f"Generating {num_runs} JSON outputs...")
    json_prompt = "Generate a JSON object with name, age, and active fields:"
    json_outputs = []
    for i in range(num_runs):
        text, _ = client.generate(json_prompt)
        json_outputs.append(text)
    
    print(f"Generating {num_runs} YAML outputs...")
    yaml_prompt = "Generate a YAML mapping with name, age, and active fields:"
    yaml_outputs = []
    for i in range(num_runs):
        text, _ = client.generate(yaml_prompt)
        yaml_outputs.append(text)
    
    # Analyze
    print("\n" + "=" * 80)
    print("VARIANCE ANALYSIS")
    print("=" * 80)
    
    json_variance = quantifier.calculate_variance(json_outputs)
    yaml_variance = quantifier.calculate_variance(yaml_outputs)
    
    print("\nJSON Results:")
    print(f"  Unique outputs: {json_variance['unique_count']}/{json_variance['total_runs']}")
    print(f"  Uniqueness ratio: {json_variance['uniqueness_ratio']:.2%}")
    print(f"  Structural variance: {json_variance['structural_variance']:.2%}")
    print(f"  Mean edit distance: {json_variance['edit_distance_mean']:.4f}")
    
    print("\nYAML Results:")
    print(f"  Unique outputs: {yaml_variance['unique_count']}/{yaml_variance['total_runs']}")
    print(f"  Uniqueness ratio: {yaml_variance['uniqueness_ratio']:.2%}")
    print(f"  Structural variance: {yaml_variance['structural_variance']:.2%}")
    print(f"  Mean edit distance: {yaml_variance['edit_distance_mean']:.4f}")
    
    if json_variance['uniqueness_ratio'] > 0:
        variance_ratio = yaml_variance['uniqueness_ratio'] / json_variance['uniqueness_ratio']
        print(f"\n  YAML variance is {variance_ratio:.2f}x higher than JSON")
    
    # Show samples
    print("\n" + "=" * 80)
    print("SAMPLE OUTPUTS")
    print("=" * 80)
    
    print("\nJSON samples (showing all unique variants):")
    unique_json = list(set(json_outputs))
    for i, output in enumerate(unique_json[:5], 1):
        print(f"  {i}. {output}")
    
    print("\nYAML samples (showing all unique variants):")
    unique_yaml = list(set(yaml_outputs))
    for i, output in enumerate(unique_yaml[:7], 1):
        print(f"  {i}. {output}")
    
    # Structural consistency
    print("\n" + "=" * 80)
    print("STRUCTURAL CONSISTENCY")
    print("=" * 80)
    
    print("\nNormalizing outputs (parsing and re-serializing)...")
    
    json_normalized = []
    json_parse_errors = 0
    for output in json_outputs:
        try:
            parsed = json.loads(output)
            normalized = json.dumps(parsed, sort_keys=True)
            json_normalized.append(normalized)
        except Exception as e:
            json_parse_errors += 1
    
    yaml_normalized = []
    yaml_parse_errors = 0
    for output in yaml_outputs:
        try:
            parsed = yaml.safe_load(output)
            if parsed:
                normalized = yaml.dump(parsed, sort_keys=True, default_flow_style=False)
                yaml_normalized.append(normalized)
        except Exception as e:
            yaml_parse_errors += 1
    
    print(f"\nJSON:")
    print(f"  Parse errors: {json_parse_errors}/{num_runs}")
    print(f"  Unique after normalization: {len(set(json_normalized))}/{len(json_normalized)}")
    print(f"  Structural consistency: {(1 - len(set(json_normalized))/len(json_normalized)):.1%}" if json_normalized else "  N/A")
    
    print(f"\nYAML:")
    print(f"  Parse errors: {yaml_parse_errors}/{num_runs}")
    print(f"  Unique after normalization: {len(set(yaml_normalized))}/{len(yaml_normalized)}")
    print(f"  Structural consistency: {(1 - len(set(yaml_normalized))/len(yaml_normalized)):.1%}" if yaml_normalized else "  N/A")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nKey Finding: YAML shows {variance_ratio:.2f}x higher output variance than JSON")
    print("This demonstrates how YAML's flexible grammar creates multiple valid")
    print("representations, while JSON's rigid grammar constrains outputs to a")
    print("single canonical form (with minor formatting differences).")


if __name__ == "__main__":
    run_demo()

