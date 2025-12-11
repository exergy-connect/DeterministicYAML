"""
Analyze logit distributions and token probabilities at specific positions.

This script demonstrates how JSON's rigid grammar creates sharp probability
distributions while YAML's flexible grammar creates flatter distributions.
"""

import numpy as np
from scipy.stats import entropy
from typing import Dict, List, Tuple

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def calculate_entropy(probabilities: Dict[str, float]) -> float:
    """Calculate Shannon entropy of a probability distribution."""
    probs = np.array(list(probabilities.values()))
    probs = probs[probs > 0]  # Remove zeros
    if len(probs) == 0:
        return 0.0
    return entropy(probs, base=2)


def simulate_json_token_probs(position: str) -> Dict[str, float]:
    """
    Simulate token probabilities for JSON at a given position.
    
    Based on training data patterns and grammar constraints.
    """
    if position == "after_open_brace":
        # After '{', must be '"' (key) or '}' (empty)
        return {
            '"': 0.95,  # Start of key (high probability)
            '}': 0.04,  # Empty object (low probability)
            '\n': 0.01,  # Formatting
        }
    
    elif position == "after_quoted_key":
        # After '"key"', must be ':'
        return {
            ':': 0.98,  # Key-value separator (near-deterministic)
            ',': 0.01,  # Trailing comma (rare, invalid in strict JSON)
            '\n': 0.01,  # Formatting
        }
    
    elif position == "after_colon":
        # After ':', value type determines next token
        # Assuming string value
        return {
            '"': 0.92,  # Start of string value
            '{': 0.04,  # Nested object
            '[': 0.02,  # Array
            'true': 0.01,  # Boolean
            'false': 0.005,
            'null': 0.005,
        }
    
    elif position == "after_string_value":
        # After '"value"', must be ',' or '}'
        return {
            ',': 0.55,  # More items
            '}': 0.44,  # End of object
            '\n': 0.01,  # Formatting
        }
    
    else:
        return {}


def simulate_yaml_token_probs(position: str) -> Dict[str, float]:
    """
    Simulate token probabilities for YAML at a given position.
    
    Based on flexible grammar and multiple valid continuations.
    """
    if position == "after_unquoted_key":
        # After 'key', can be ':', '-', or indentation-based
        return {
            ':': 0.45,  # Key-value mapping
            '-': 0.38,  # List item
            ' ': 0.10,  # Indentation (nested)
            '\n': 0.05,  # Newline (block style)
            ',': 0.02,  # Flow style
        }
    
    elif position == "after_colon":
        # After 'key:', value can be unquoted, quoted, or block
        return {
            'value': 0.35,  # Unquoted scalar (most common)
            '"value"': 0.28,  # Double-quoted
            "'value'": 0.22,  # Single-quoted
            '|': 0.10,  # Literal block
            '>': 0.05,  # Folded block
        }
    
    elif position == "after_string_value":
        # After value, can continue in multiple ways
        return {
            '\n': 0.40,  # New key (block style)
            ',': 0.25,  # More items (flow style)
            ' ': 0.20,  # Inline continuation
            '#': 0.10,  # Comment
            '---': 0.05,  # Document separator
        }
    
    else:
        return {}


def compare_distributions():
    """Compare JSON and YAML probability distributions."""
    positions = [
        ("after_open_brace", "after_unquoted_key"),
        ("after_quoted_key", "after_colon"),
        ("after_colon", "after_colon"),
        ("after_string_value", "after_string_value"),
    ]
    
    print("=" * 80)
    print("TOKEN PROBABILITY DISTRIBUTION COMPARISON")
    print("=" * 80)
    
    results = []
    
    for json_pos, yaml_pos in positions:
        json_probs = simulate_json_token_probs(json_pos)
        yaml_probs = simulate_yaml_token_probs(yaml_pos)
        
        json_entropy = calculate_entropy(json_probs)
        yaml_entropy = calculate_entropy(yaml_probs)
        
        json_top_prob = max(json_probs.values()) if json_probs else 0
        yaml_top_prob = max(yaml_probs.values()) if yaml_probs else 0
        
        print(f"\nPosition: {json_pos} (JSON) vs {yaml_pos} (YAML)")
        print(f"  JSON entropy: {json_entropy:.3f} bits")
        print(f"  YAML entropy: {yaml_entropy:.3f} bits")
        print(f"  Entropy ratio: {yaml_entropy / json_entropy:.2f}x" if json_entropy > 0 else "  N/A")
        print(f"  JSON top token prob: {json_top_prob:.3f}")
        print(f"  YAML top token prob: {yaml_top_prob:.3f}")
        
        print(f"\n  JSON top 3 tokens:")
        for token, prob in sorted(json_probs.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"    {repr(token):20s} {prob:.4f}")
        
        print(f"  YAML top 3 tokens:")
        for token, prob in sorted(yaml_probs.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"    {repr(token):20s} {prob:.4f}")
        
        results.append({
            'position': json_pos,
            'json_entropy': json_entropy,
            'yaml_entropy': yaml_entropy,
            'json_top_prob': json_top_prob,
            'yaml_top_prob': yaml_top_prob,
        })
    
    return results


def visualize_distributions():
    """Create visualizations of probability distributions."""
    if not HAS_MATPLOTLIB:
        print("Skipping visualization (matplotlib/seaborn not available)")
        return
    
    positions = [
        ("after_open_brace", "after_unquoted_key", "After opening/start"),
        ("after_colon", "after_colon", "After colon separator"),
    ]
    
    fig, axes = plt.subplots(len(positions), 2, figsize=(14, 6))
    fig.suptitle('Token Probability Distributions: JSON vs YAML', fontsize=14, fontweight='bold')
    
    for idx, (json_pos, yaml_pos, title) in enumerate(positions):
        json_probs = simulate_json_token_probs(json_pos)
        yaml_probs = simulate_yaml_token_probs(yaml_pos)
        
        # JSON plot
        ax_json = axes[idx, 0]
        tokens = list(json_probs.keys())
        probs = list(json_probs.values())
        ax_json.bar(range(len(tokens)), probs, color='steelblue', alpha=0.7)
        ax_json.set_xticks(range(len(tokens)))
        ax_json.set_xticklabels([repr(t)[:10] for t in tokens], rotation=45, ha='right')
        ax_json.set_ylabel('Probability')
        ax_json.set_title(f'JSON: {title}')
        ax_json.set_ylim(0, 1.0)
        ax_json.grid(axis='y', alpha=0.3)
        
        # Add entropy annotation
        json_entropy = calculate_entropy(json_probs)
        ax_json.text(0.02, 0.98, f'H = {json_entropy:.3f} bits', 
                    transform=ax_json.transAxes, 
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # YAML plot
        ax_yaml = axes[idx, 1]
        tokens = list(yaml_probs.keys())
        probs = list(yaml_probs.values())
        ax_yaml.bar(range(len(tokens)), probs, color='coral', alpha=0.7)
        ax_yaml.set_xticks(range(len(tokens)))
        ax_yaml.set_xticklabels([repr(t)[:10] for t in tokens], rotation=45, ha='right')
        ax_yaml.set_ylabel('Probability')
        ax_yaml.set_title(f'YAML: {title}')
        ax_yaml.set_ylim(0, 1.0)
        ax_yaml.grid(axis='y', alpha=0.3)
        
        # Add entropy annotation
        yaml_entropy = calculate_entropy(yaml_probs)
        ax_yaml.text(0.02, 0.98, f'H = {yaml_entropy:.3f} bits', 
                     transform=ax_yaml.transAxes, 
                     verticalalignment='top',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('token_probability_comparison.png', dpi=150, bbox_inches='tight')
    print("\nSaved visualization to 'token_probability_comparison.png'")
    plt.close()


def analyze_decoding_impact():
    """Analyze how different decoding methods affect output variance."""
    print("\n" + "=" * 80)
    print("DECODING METHOD IMPACT ANALYSIS")
    print("=" * 80)
    
    # Simulate probability distributions
    json_probs = simulate_json_token_probs("after_open_brace")
    yaml_probs = simulate_yaml_token_probs("after_unquoted_key")
    
    def apply_temperature(probs: Dict[str, float], temp: float) -> Dict[str, float]:
        """Apply temperature scaling to probabilities."""
        if temp == 0:
            # Greedy: return one-hot
            top_token = max(probs.items(), key=lambda x: x[1])[0]
            return {top_token: 1.0}
        
        # Temperature scaling: p' = exp(log(p) / T) / Z
        log_probs = {k: np.log(v) for k, v in probs.items()}
        scaled = {k: np.exp(v / temp) for k, v in log_probs.items()}
        total = sum(scaled.values())
        return {k: v / total for k, v in scaled.items()}
    
    def calculate_variance_metric(probs: Dict[str, float]) -> float:
        """Calculate a variance metric (1 - top_prob)."""
        top_prob = max(probs.values())
        return 1.0 - top_prob
    
    temperatures = [0.0, 0.1, 0.5, 1.0, 2.0]
    
    print("\nJSON (after '{'):")
    print(f"{'Temperature':<12} {'Top Prob':<12} {'Variance Metric':<15} {'Entropy':<10}")
    print("-" * 50)
    for temp in temperatures:
        scaled = apply_temperature(json_probs, temp)
        top_prob = max(scaled.values())
        variance = calculate_variance_metric(scaled)
        ent = calculate_entropy(scaled)
        print(f"{temp:<12.1f} {top_prob:<12.4f} {variance:<15.4f} {ent:<10.3f}")
    
    print("\nYAML (after 'key'):")
    print(f"{'Temperature':<12} {'Top Prob':<12} {'Variance Metric':<15} {'Entropy':<10}")
    print("-" * 50)
    for temp in temperatures:
        scaled = apply_temperature(yaml_probs, temp)
        top_prob = max(scaled.values())
        variance = calculate_variance_metric(scaled)
        ent = calculate_entropy(scaled)
        print(f"{temp:<12.1f} {top_prob:<12.4f} {variance:<15.4f} {ent:<10.3f}")
    
    # Calculate amplification
    print("\nVariance Amplification (YAML/JSON ratio):")
    print(f"{'Temperature':<12} {'Amplification':<15}")
    print("-" * 30)
    for temp in temperatures:
        json_scaled = apply_temperature(json_probs, temp)
        yaml_scaled = apply_temperature(yaml_probs, temp)
        json_var = calculate_variance_metric(json_scaled)
        yaml_var = calculate_variance_metric(yaml_scaled)
        if json_var > 0:
            amplification = yaml_var / json_var
            print(f"{temp:<12.1f} {amplification:<15.2f}")


def main():
    """Run all analyses."""
    print("Analyzing logit distributions and token probabilities...\n")
    
    results = compare_distributions()
    
    analyze_decoding_impact()
    
    try:
        visualize_distributions()
    except Exception as e:
        print(f"\nWarning: Could not generate visualization: {e}")
        print("(This requires matplotlib/seaborn)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    avg_json_entropy = np.mean([r['json_entropy'] for r in results])
    avg_yaml_entropy = np.mean([r['yaml_entropy'] for r in results])
    
    avg_json_top = np.mean([r['json_top_prob'] for r in results])
    avg_yaml_top = np.mean([r['yaml_top_prob'] for r in results])
    
    print(f"\nAverage entropy:")
    print(f"  JSON: {avg_json_entropy:.3f} bits")
    print(f"  YAML: {avg_yaml_entropy:.3f} bits")
    print(f"  Ratio: {avg_yaml_entropy / avg_json_entropy:.2f}x")
    
    print(f"\nAverage top token probability:")
    print(f"  JSON: {avg_json_top:.3f}")
    print(f"  YAML: {avg_yaml_top:.3f}")
    print(f"  Difference: {avg_json_top - avg_yaml_top:.3f}")


if __name__ == "__main__":
    main()

