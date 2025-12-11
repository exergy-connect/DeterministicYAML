"""
Main script to run quantification experiments.

This script demonstrates:
1. Variance comparison between JSON and YAML
2. Token probability analysis
3. Decoding method comparison
4. Entropy calculations
"""

import os
import sys
from quantify_differences import LLMQuantifier
from openai_client import OpenAIClient
import json
import yaml
from collections import Counter


def run_variance_experiment(client, num_runs: int = 20):
    """Run variance experiment comparing JSON and YAML outputs."""
    print("=" * 80)
    print("VARIANCE EXPERIMENT")
    print("=" * 80)
    print(f"Running {num_runs} generations for each format...\n")
    
    quantifier = LLMQuantifier(client)
    
    # JSON prompt
    json_prompt = """Generate a JSON object with the following structure:
- A "name" field (string)
- An "age" field (number)
- A "active" field (boolean)"""
    
    # YAML prompt
    yaml_prompt = """Generate a YAML mapping with the following structure:
- A "name" field (string)
- An "age" field (number)
- A "active" field (boolean)"""
    
    print("Generating JSON outputs...")
    json_outputs = []
    for i in range(num_runs):
        text, _ = client.generate(json_prompt, max_tokens=50, temperature=1.0)
        json_outputs.append(text.strip())
        if (i + 1) % 5 == 0:
            print(f"  Completed {i + 1}/{num_runs}")
    
    print("\nGenerating YAML outputs...")
    yaml_outputs = []
    for i in range(num_runs):
        text, _ = client.generate(yaml_prompt, max_tokens=50, temperature=1.0)
        yaml_outputs.append(text.strip())
        if (i + 1) % 5 == 0:
            print(f"  Completed {i + 1}/{num_runs}")
    
    # Analyze variance
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
    
    # Show sample outputs
    print("\n" + "=" * 80)
    print("SAMPLE OUTPUTS")
    print("=" * 80)
    
    print("\nJSON samples (first 5):")
    for i, output in enumerate(json_outputs[:5], 1):
        print(f"  {i}. {output[:100]}...")
    
    print("\nYAML samples (first 5):")
    for i, output in enumerate(yaml_outputs[:5], 1):
        print(f"  {i}. {output[:100]}...")
    
    return json_outputs, yaml_outputs, json_variance, yaml_variance


def run_token_probability_experiment(client):
    """Analyze token probability distributions."""
    print("\n" + "=" * 80)
    print("TOKEN PROBABILITY EXPERIMENT")
    print("=" * 80)
    
    # Test positions where structure constrains continuation
    test_cases = [
        {
            'name': 'JSON: After opening brace',
            'prompt': 'Generate a JSON object:\n{',
            'format': 'json'
        },
        {
            'name': 'JSON: After quoted key',
            'prompt': 'Generate a JSON object:\n{"name"',
            'format': 'json'
        },
        {
            'name': 'YAML: After unquoted key',
            'prompt': 'Generate a YAML mapping:\nname',
            'format': 'yaml'
        },
        {
            'name': 'YAML: After key with colon',
            'prompt': 'Generate a YAML mapping:\nname:',
            'format': 'yaml'
        },
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"  Prompt: {repr(test_case['prompt'])}")
        
        try:
            probs = client.get_next_token_probs(test_case['prompt'], top_k=10)
            
            if probs:
                # Calculate entropy
                import numpy as np
                from scipy.stats import entropy
                prob_array = np.array(list(probs.values()))
                prob_array = prob_array[prob_array > 0]
                h = entropy(prob_array, base=2)
                
                print(f"  Entropy: {h:.3f} bits")
                print(f"  Top 5 tokens:")
                for token, prob in sorted(probs.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"    {repr(token):20s} {prob:.4f} ({prob*100:.1f}%)")
                
                top_token_prob = max(probs.values())
                print(f"  Top token probability: {top_token_prob:.4f} ({top_token_prob*100:.1f}%)")
                
                results.append({
                    'test': test_case['name'],
                    'format': test_case['format'],
                    'entropy': h,
                    'top_token_prob': top_token_prob,
                    'num_tokens': len(probs)
                })
            else:
                print("  No probabilities returned")
        
        except Exception as e:
            print(f"  Error: {e}")
    
    return results


def run_decoding_method_experiment(client, num_runs: int = 10):
    """Compare different decoding methods."""
    print("\n" + "=" * 80)
    print("DECODING METHOD EXPERIMENT")
    print("=" * 80)
    
    json_prompt = "Generate a JSON object with a 'name' key:"
    yaml_prompt = "Generate a YAML mapping with a 'name' key:"
    
    methods = {
        'greedy': {'temperature': 0.0, 'top_p': 1.0},
        'temp_0.1': {'temperature': 0.1, 'top_p': 1.0},
        'temp_1.0': {'temperature': 1.0, 'top_p': 1.0},
        'temp_2.0': {'temperature': 2.0, 'top_p': 1.0},
        'top_p_0.95': {'temperature': 1.0, 'top_p': 0.95},
    }
    
    quantifier = LLMQuantifier(client)
    
    print("\nJSON Results:")
    json_results = {}
    for method_name, params in methods.items():
        outputs = []
        for _ in range(num_runs):
            text, _ = client.generate(json_prompt, max_tokens=30, **params)
            outputs.append(text.strip())
        
        variance = quantifier.calculate_variance(outputs)
        unique_count = len(set(outputs))
        json_results[method_name] = {
            'unique_count': unique_count,
            'uniqueness_ratio': variance['uniqueness_ratio']
        }
        print(f"  {method_name:15s} Unique: {unique_count}/{num_runs} ({variance['uniqueness_ratio']:.1%})")
    
    print("\nYAML Results:")
    yaml_results = {}
    for method_name, params in methods.items():
        outputs = []
        for _ in range(num_runs):
            text, _ = client.generate(yaml_prompt, max_tokens=30, **params)
            outputs.append(text.strip())
        
        variance = quantifier.calculate_variance(outputs)
        unique_count = len(set(outputs))
        yaml_results[method_name] = {
            'unique_count': unique_count,
            'uniqueness_ratio': variance['uniqueness_ratio']
        }
        print(f"  {method_name:15s} Unique: {unique_count}/{num_runs} ({variance['uniqueness_ratio']:.1%})")
    
    # Compare variance amplification
    print("\nVariance Amplification (YAML/JSON ratio):")
    for method_name in methods.keys():
        if method_name in json_results and method_name in yaml_results:
            json_ratio = json_results[method_name]['uniqueness_ratio']
            yaml_ratio = yaml_results[method_name]['uniqueness_ratio']
            if json_ratio > 0:
                amplification = yaml_ratio / json_ratio
                print(f"  {method_name:15s} {amplification:.2f}x")
    
    return json_results, yaml_results


def run_structural_consistency_experiment(client):
    """Test structural consistency (same logical content, different syntax)."""
    print("\n" + "=" * 80)
    print("STRUCTURAL CONSISTENCY EXPERIMENT")
    print("=" * 80)
    
    # Generate same logical structure multiple times
    json_prompt = "Generate a JSON object with name='John', age=30, active=true:"
    yaml_prompt = "Generate a YAML mapping with name='John', age=30, active=true:"
    
    num_runs = 15
    
    print(f"\nGenerating {num_runs} JSON outputs...")
    json_outputs = []
    for _ in range(num_runs):
        text, _ = client.generate(json_prompt, max_tokens=50, temperature=1.0)
        json_outputs.append(text.strip())
    
    print(f"Generating {num_runs} YAML outputs...")
    yaml_outputs = []
    for _ in range(num_runs):
        text, _ = client.generate(yaml_prompt, max_tokens=50, temperature=1.0)
        yaml_outputs.append(text.strip())
    
    # Normalize and compare
    print("\nNormalizing outputs (parsing and re-serializing)...")
    
    json_normalized = []
    json_parse_errors = 0
    for output in json_outputs:
        try:
            parsed = json.loads(output)
            normalized = json.dumps(parsed, sort_keys=True)
            json_normalized.append(normalized)
        except:
            json_parse_errors += 1
    
    yaml_normalized = []
    yaml_parse_errors = 0
    for output in yaml_outputs:
        try:
            parsed = yaml.safe_load(output)
            if parsed:
                normalized = yaml.dump(parsed, sort_keys=True, default_flow_style=False)
                yaml_normalized.append(normalized)
        except:
            yaml_parse_errors += 1
    
    print(f"\nJSON:")
    print(f"  Parse errors: {json_parse_errors}/{num_runs}")
    print(f"  Unique after normalization: {len(set(json_normalized))}/{len(json_normalized)}")
    
    print(f"\nYAML:")
    print(f"  Parse errors: {yaml_parse_errors}/{num_runs}")
    print(f"  Unique after normalization: {len(set(yaml_normalized))}/{len(yaml_normalized)}")
    
    # Show structural variants
    if yaml_normalized:
        print("\nYAML structural variants (first 5 unique):")
        for i, variant in enumerate(list(set(yaml_normalized))[:5], 1):
            print(f"  {i}. {variant[:80]}...")


def main():
    """Run all experiments."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Initialize client
    print("Initializing OpenAI client...")
    client = OpenAIClient(model="gpt-4o-mini", api_key=api_key)
    
    try:
        # Run experiments
        json_outputs, yaml_outputs, json_var, yaml_var = run_variance_experiment(client, num_runs=20)
        
        token_probs = run_token_probability_experiment(client)
        
        json_decoding, yaml_decoding = run_decoding_method_experiment(client, num_runs=10)
        
        run_structural_consistency_experiment(client)
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"\nJSON variance ratio: {json_var['uniqueness_ratio']:.2%}")
        print(f"YAML variance ratio: {yaml_var['uniqueness_ratio']:.2%}")
        if json_var['uniqueness_ratio'] > 0:
            print(f"YAML is {yaml_var['uniqueness_ratio'] / json_var['uniqueness_ratio']:.2f}x more variable")
        
        if token_probs:
            json_entropy = [r['entropy'] for r in token_probs if r['format'] == 'json']
            yaml_entropy = [r['entropy'] for r in token_probs if r['format'] == 'yaml']
            if json_entropy and yaml_entropy:
                print(f"\nAverage entropy:")
                print(f"  JSON: {sum(json_entropy)/len(json_entropy):.3f} bits")
                print(f"  YAML: {sum(yaml_entropy)/len(yaml_entropy):.3f} bits")
        
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user.")
    except Exception as e:
        print(f"\n\nError running experiments: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

