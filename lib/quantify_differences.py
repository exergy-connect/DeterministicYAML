"""
Quantify differences between JSON and YAML generation in LLMs.

This script measures:
- Output variance across multiple runs
- Token probability distributions (entropy)
- Decoding method behavior
- Structural consistency
"""

import json
import yaml
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
import statistics
from scipy.stats import entropy


class LLMQuantifier:
    """Quantify LLM behavior differences between JSON and YAML."""
    
    def __init__(self, model_client=None):
        """
        Initialize with an LLM client.
        
        Args:
            model_client: Object with a `generate()` method that returns
                         (text, logprobs_dict) where logprobs_dict contains
                         token probabilities at each position.
        """
        self.client = model_client
        self.json_outputs = []
        self.yaml_outputs = []
        self.json_logprobs = []
        self.yaml_logprobs = []
    
    def generate_json(self, prompt: str, num_runs: int = 10, **kwargs) -> List[str]:
        """Generate JSON outputs multiple times."""
        outputs = []
        for _ in range(num_runs):
            if self.client:
                text, _ = self.client.generate(prompt, **kwargs)
            else:
                # Mock for demonstration
                text = '{"name": "value"}'
            outputs.append(text)
        self.json_outputs.extend(outputs)
        return outputs
    
    def generate_yaml(self, prompt: str, num_runs: int = 10, **kwargs) -> List[str]:
        """Generate YAML outputs multiple times."""
        outputs = []
        for _ in range(num_runs):
            if self.client:
                text, _ = self.client.generate(prompt, **kwargs)
            else:
                # Mock for demonstration
                text = 'name: value'
            outputs.append(text)
        self.yaml_outputs.extend(outputs)
        return outputs
    
    def calculate_variance(self, outputs: List[str]) -> Dict[str, float]:
        """
        Calculate variance metrics for a set of outputs.
        
        Returns:
            - unique_count: Number of unique outputs
            - structural_variance: Variance in structure (not just values)
            - edit_distance_mean: Mean edit distance between outputs
        """
        unique_outputs = set(outputs)
        unique_count = len(unique_outputs)
        uniqueness_ratio = unique_count / len(outputs) if outputs else 0
        
        # Structural variance: compare normalized forms
        normalized = []
        for output in outputs:
            try:
                # Parse and re-serialize to normalize
                if output.strip().startswith('{') or output.strip().startswith('['):
                    parsed = json.loads(output)
                    normalized.append(json.dumps(parsed, sort_keys=True))
                else:
                    parsed = yaml.safe_load(output)
                    normalized.append(yaml.dump(parsed, sort_keys=True, default_flow_style=False))
            except:
                normalized.append(output)
        
        structural_unique = len(set(normalized))
        structural_variance = structural_unique / len(normalized) if normalized else 0
        
        # Edit distance (Levenshtein-like, simplified)
        if len(outputs) > 1:
            edit_distances = []
            for i in range(len(outputs)):
                for j in range(i + 1, len(outputs)):
                    dist = self._simple_edit_distance(outputs[i], outputs[j])
                    edit_distances.append(dist)
            edit_distance_mean = statistics.mean(edit_distances) if edit_distances else 0
        else:
            edit_distance_mean = 0
        
        return {
            'unique_count': unique_count,
            'uniqueness_ratio': uniqueness_ratio,
            'structural_unique': structural_unique,
            'structural_variance': structural_variance,
            'edit_distance_mean': edit_distance_mean,
            'total_runs': len(outputs)
        }
    
    def _simple_edit_distance(self, s1: str, s2: str) -> float:
        """Simple character-level edit distance (normalized)."""
        if not s1 or not s2:
            return 1.0
        
        # Use set difference for simplicity
        set1 = set(s1)
        set2 = set(s2)
        union = set1 | set2
        intersection = set1 & set2
        
        if not union:
            return 0.0
        
        return 1.0 - (len(intersection) / len(union))
    
    def calculate_entropy_from_logprobs(self, logprobs_list: List[Dict[str, float]]) -> List[float]:
        """
        Calculate entropy at each token position from logprobs.
        
        Args:
            logprobs_list: List of dicts, each mapping token -> logprob
        
        Returns:
            List of entropy values (one per position)
        """
        if not logprobs_list:
            return []
        
        entropies = []
        max_positions = max(len(lp) for lp in logprobs_list) if logprobs_list else 0
        
        for pos in range(max_positions):
            # Collect all tokens and their probabilities at this position
            token_probs = defaultdict(list)
            
            for logprobs in logprobs_list:
                if pos < len(logprobs):
                    for token, logprob in logprobs[pos].items():
                        prob = np.exp(logprob)  # Convert logprob to prob
                        token_probs[token].append(prob)
            
            # Average probabilities across runs for each token
            avg_probs = {token: np.mean(probs) for token, probs in token_probs.items()}
            
            # Normalize to probability distribution
            total = sum(avg_probs.values())
            if total > 0:
                normalized = {token: prob / total for token, prob in avg_probs.items()}
                # Calculate entropy: H = -Σ p(x) * log2(p(x))
                probs_array = np.array(list(normalized.values()))
                probs_array = probs_array[probs_array > 0]  # Remove zeros
                h = entropy(probs_array, base=2)
                entropies.append(h)
            else:
                entropies.append(0.0)
        
        return entropies
    
    def analyze_token_probabilities(self, prompt: str, format_type: str = 'json') -> Dict[str, Any]:
        """
        Analyze token probability distributions after a prompt.
        
        Returns token probabilities, entropy, and top-k diversity.
        """
        if not self.client:
            return {'error': 'No client provided'}
        
        # Get logprobs for next few tokens
        _, logprobs = self.client.generate(
            prompt,
            max_tokens=1,
            logprobs=5,  # Top 5 tokens
            return_logprobs=True
        )
        
        if not logprobs:
            return {'error': 'No logprobs returned'}
        
        # Convert logprobs to probabilities
        probs = {token: np.exp(logprob) for token, logprob in logprobs.items()}
        total = sum(probs.values())
        normalized = {token: prob / total for token, prob in probs.items()}
        
        # Calculate entropy
        prob_array = np.array(list(normalized.values()))
        prob_array = prob_array[prob_array > 0]
        h = entropy(prob_array, base=2)
        
        # Top token probability
        top_token = max(normalized.items(), key=lambda x: x[1])
        
        return {
            'format': format_type,
            'token_probabilities': normalized,
            'entropy': h,
            'top_token': top_token[0],
            'top_token_prob': top_token[1],
            'num_tokens': len(normalized)
        }
    
    def compare_decoding_methods(self, prompt: str, format_type: str = 'json') -> Dict[str, Any]:
        """
        Compare outputs across different decoding methods.
        
        Returns variance metrics for each method.
        """
        methods = {
            'greedy': {'temperature': 0.0, 'top_p': 1.0},
            'temp_low': {'temperature': 0.1, 'top_p': 1.0},
            'temp_high': {'temperature': 2.0, 'top_p': 1.0},
            'top_p_95': {'temperature': 1.0, 'top_p': 0.95},
            'top_p_50': {'temperature': 1.0, 'top_p': 0.50},
        }
        
        results = {}
        
        for method_name, params in methods.items():
            outputs = []
            for _ in range(10):  # 10 runs per method
                if self.client:
                    text, _ = self.client.generate(prompt, **params)
                else:
                    text = f'{{"name": "value_{method_name}"}}' if format_type == 'json' else f'name: value_{method_name}'
                outputs.append(text)
            
            variance_metrics = self.calculate_variance(outputs)
            results[method_name] = {
                'variance_metrics': variance_metrics,
                'sample_outputs': outputs[:3]  # First 3 as samples
            }
        
        return {
            'format': format_type,
            'methods': results
        }
    
    def generate_comparison_report(self) -> str:
        """Generate a comprehensive comparison report."""
        if not self.json_outputs and not self.yaml_outputs:
            return "No outputs to compare. Run generate_json() and generate_yaml() first."
        
        report = []
        report.append("=" * 80)
        report.append("JSON vs YAML LLM Output Comparison")
        report.append("=" * 80)
        report.append("")
        
        if self.json_outputs:
            json_variance = self.calculate_variance(self.json_outputs)
            report.append("JSON Variance Metrics:")
            report.append(f"  Unique outputs: {json_variance['unique_count']}/{json_variance['total_runs']} ({json_variance['uniqueness_ratio']:.2%})")
            report.append(f"  Structural variance: {json_variance['structural_variance']:.2%}")
            report.append(f"  Mean edit distance: {json_variance['edit_distance_mean']:.4f}")
            report.append("")
        
        if self.yaml_outputs:
            yaml_variance = self.calculate_variance(self.yaml_outputs)
            report.append("YAML Variance Metrics:")
            report.append(f"  Unique outputs: {yaml_variance['unique_count']}/{yaml_variance['total_runs']} ({yaml_variance['uniqueness_ratio']:.2%})")
            report.append(f"  Structural variance: {yaml_variance['structural_variance']:.2%}")
            report.append(f"  Mean edit distance: {yaml_variance['edit_distance_mean']:.4f}")
            report.append("")
        
        if self.json_outputs and self.yaml_outputs:
            report.append("Comparison:")
            json_ratio = self.calculate_variance(self.json_outputs)['uniqueness_ratio']
            yaml_ratio = self.calculate_variance(self.yaml_outputs)['uniqueness_ratio']
            variance_ratio = yaml_ratio / json_ratio if json_ratio > 0 else float('inf')
            report.append(f"  YAML variance is {variance_ratio:.2f}x higher than JSON variance")
            report.append("")
        
        return "\n".join(report)


def main():
    """Example usage."""
    print("LLM JSON vs YAML Quantification")
    print("=" * 80)
    print("\nNote: This script requires an LLM client implementation.")
    print("See openai_client.py or anthropic_client.py for examples.\n")
    
    # Create quantifier (without client for demo)
    quantifier = LLMQuantifier()
    
    # Example: Generate outputs
    json_prompt = "Generate a JSON object with a 'name' key:"
    yaml_prompt = "Generate a YAML mapping with a 'name' key:"
    
    print("Generating JSON outputs...")
    json_outputs = quantifier.generate_json(json_prompt, num_runs=5)
    
    print("Generating YAML outputs...")
    yaml_outputs = quantifier.generate_yaml(yaml_prompt, num_runs=5)
    
    # Generate report
    report = quantifier.generate_comparison_report()
    print(report)


if __name__ == "__main__":
    main()

