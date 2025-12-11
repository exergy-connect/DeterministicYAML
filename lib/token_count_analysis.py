"""
Analyze token count differences between JSON and YAML.

This measures:
- Token count for equivalent structures
- Token efficiency (tokens per data point)
- Tokenization boundary differences
- Impact on generation cost

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

import json
import yaml
from typing import Dict, List, Any, Tuple
import statistics
import re

# Try to import tiktoken, fallback to approximation
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False


class TokenCountAnalyzer:
    """Analyze token count differences between JSON and YAML."""
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        Initialize with a tokenizer.
        
        Args:
            encoding_name: tiktoken encoding name (cl100k_base for GPT-4, etc.)
        """
        self.encoding = None
        self.encoding_name = encoding_name
        
        if HAS_TIKTOKEN:
            try:
                self.encoding = tiktoken.get_encoding(encoding_name)
            except:
                self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            print("Note: tiktoken not available, using approximation (chars/4)")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Approximation: ~4 chars per token (rough average for English/code)
            # This is a simplified approximation
            return len(text) // 4 + (1 if len(text) % 4 > 0 else 0)
    
    def tokenize(self, text: str) -> List[str]:
        """Get list of tokens."""
        if self.encoding:
            return [self.encoding.decode([token]) for token in self.encoding.encode(text)]
        else:
            # Approximation: split by whitespace and punctuation
            # This is not accurate but gives a sense of token boundaries
            tokens = re.findall(r'\S+|\s+', text)
            return [t for t in tokens if t.strip() or t in [' ', '\n', '\t']]
    
    def compare_equivalent_structures(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare token counts for equivalent JSON and YAML structures.
        
        Args:
            data: Python dict to serialize
        
        Returns:
            Comparison metrics
        """
        # Generate JSON
        json_str = json.dumps(data, indent=2)
        json_compact = json.dumps(data)
        
        # Generate YAML
        yaml_str = yaml.dump(data, default_flow_style=False)
        yaml_flow = yaml.dump(data, default_flow_style=True)
        
        # Count tokens
        json_tokens = self.count_tokens(json_str)
        json_compact_tokens = self.count_tokens(json_compact)
        yaml_tokens = self.count_tokens(yaml_str)
        yaml_flow_tokens = self.count_tokens(yaml_flow)
        
        # Tokenize to see boundaries
        json_token_list = self.tokenize(json_str)
        yaml_token_list = self.tokenize(yaml_str)
        
        return {
            'data': data,
            'json': {
                'pretty': {
                    'text': json_str,
                    'tokens': json_tokens,
                    'token_list': json_token_list[:20]  # First 20 tokens
                },
                'compact': {
                    'text': json_compact,
                    'tokens': json_compact_tokens
                }
            },
            'yaml': {
                'block': {
                    'text': yaml_str,
                    'tokens': yaml_tokens,
                    'token_list': yaml_token_list[:20]  # First 20 tokens
                },
                'flow': {
                    'text': yaml_flow,
                    'tokens': yaml_flow_tokens
                }
            },
            'comparison': {
                'json_pretty_tokens': json_tokens,
                'json_compact_tokens': json_compact_tokens,
                'yaml_block_tokens': yaml_tokens,
                'yaml_flow_tokens': yaml_flow_tokens,
                'json_vs_yaml_ratio': json_tokens / yaml_tokens if yaml_tokens > 0 else 0,
                'yaml_vs_json_ratio': yaml_tokens / json_tokens if json_tokens > 0 else 0,
                'token_difference': yaml_tokens - json_tokens,
                'token_difference_pct': ((yaml_tokens - json_tokens) / json_tokens * 100) if json_tokens > 0 else 0
            }
        }
    
    def analyze_token_efficiency(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze token efficiency across multiple test cases.
        
        Returns average token counts and efficiency metrics.
        """
        results = []
        
        for data in test_cases:
            comparison = self.compare_equivalent_structures(data)
            results.append(comparison['comparison'])
        
        # Calculate averages
        avg_json_pretty = statistics.mean([r['json_pretty_tokens'] for r in results])
        avg_json_compact = statistics.mean([r['json_compact_tokens'] for r in results])
        avg_yaml_block = statistics.mean([r['yaml_block_tokens'] for r in results])
        avg_yaml_flow = statistics.mean([r['yaml_flow_tokens'] for r in results])
        
        return {
            'num_cases': len(results),
            'averages': {
                'json_pretty': avg_json_pretty,
                'json_compact': avg_json_compact,
                'yaml_block': avg_yaml_block,
                'yaml_flow': avg_yaml_flow
            },
            'ratios': {
                'yaml_block_vs_json_pretty': avg_yaml_block / avg_json_pretty if avg_json_pretty > 0 else 0,
                'yaml_block_vs_json_compact': avg_yaml_block / avg_json_compact if avg_json_compact > 0 else 0,
                'json_compact_vs_yaml_block': avg_json_compact / avg_yaml_block if avg_yaml_block > 0 else 0
            },
            'individual_results': results
        }
    
    def analyze_token_boundaries(self, json_text: str, yaml_text: str) -> Dict[str, Any]:
        """
        Analyze how tokenization boundaries differ between JSON and YAML.
        
        This shows how the same logical content is tokenized differently.
        """
        json_tokens = self.tokenize(json_text)
        yaml_tokens = self.tokenize(yaml_text)
        
        # Count special tokens
        json_special = sum(1 for t in json_tokens if t in ['{', '}', '[', ']', ':', ',', '"'])
        yaml_special = sum(1 for t in yaml_tokens if t in [':', '-', '#', '|', '>', '{', '}'])
        
        # Count whitespace tokens
        json_whitespace = sum(1 for t in json_tokens if t.strip() == '')
        yaml_whitespace = sum(1 for t in yaml_tokens if t.strip() == '')
        
        # Average token length
        json_avg_len = statistics.mean([len(t) for t in json_tokens]) if json_tokens else 0
        yaml_avg_len = statistics.mean([len(t) for t in yaml_tokens]) if yaml_tokens else 0
        
        return {
            'json': {
                'total_tokens': len(json_tokens),
                'special_tokens': json_special,
                'whitespace_tokens': json_whitespace,
                'avg_token_length': json_avg_len,
                'sample_tokens': json_tokens[:15]
            },
            'yaml': {
                'total_tokens': len(yaml_tokens),
                'special_tokens': yaml_special,
                'whitespace_tokens': yaml_whitespace,
                'avg_token_length': yaml_avg_len,
                'sample_tokens': yaml_tokens[:15]
            },
            'differences': {
                'token_count_diff': len(yaml_tokens) - len(json_tokens),
                'special_token_diff': yaml_special - json_special,
                'whitespace_diff': yaml_whitespace - json_whitespace,
                'avg_length_diff': yaml_avg_len - json_avg_len
            }
        }
    
    def measure_generation_cost(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Measure tokens needed to generate equivalent structures.
        
        This estimates generation cost by counting tokens in the output.
        """
        json_compact = json.dumps(data)
        yaml_block = yaml.dump(data, default_flow_style=False)
        
        # Count output tokens
        json_output_tokens = self.count_tokens(json_compact)
        yaml_output_tokens = self.count_tokens(yaml_block)
        
        # Estimate prompt tokens (assuming same prompt structure)
        json_prompt = "Generate JSON:"
        yaml_prompt = "Generate YAML:"
        
        json_prompt_tokens = self.count_tokens(json_prompt)
        yaml_prompt_tokens = self.count_tokens(yaml_prompt)
        
        # Total (prompt + output)
        json_total = json_prompt_tokens + json_output_tokens
        yaml_total = yaml_prompt_tokens + yaml_output_tokens
        
        return {
            'json': {
                'prompt_tokens': json_prompt_tokens,
                'output_tokens': json_output_tokens,
                'total_tokens': json_total
            },
            'yaml': {
                'prompt_tokens': yaml_prompt_tokens,
                'output_tokens': yaml_output_tokens,
                'total_tokens': yaml_total
            },
            'comparison': {
                'output_token_diff': yaml_output_tokens - json_output_tokens,
                'output_token_ratio': yaml_output_tokens / json_output_tokens if json_output_tokens > 0 else 0,
                'total_token_diff': yaml_total - json_total,
                'total_token_ratio': yaml_total / json_total if json_total > 0 else 0
            }
        }


def run_token_count_analysis():
    """Run comprehensive token count analysis."""
    print("=" * 80)
    print("TOKEN COUNT ANALYSIS: JSON vs YAML")
    print("=" * 80)
    
    analyzer = TokenCountAnalyzer()
    
    # Test cases
    test_cases = [
        {
            'name': 'John',
            'age': 30,
            'active': True
        },
        {
            'users': [
                {'name': 'Alice', 'age': 25},
                {'name': 'Bob', 'age': 30}
            ],
            'count': 2
        },
        {
            'config': {
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'ssl': True
                },
                'cache': {
                    'ttl': 3600,
                    'enabled': True
                }
            }
        },
        {
            'description': 'A longer string value that might be tokenized differently',
            'tags': ['important', 'urgent', 'review'],
            'metadata': {
                'created': '2024-01-01',
                'updated': '2024-01-02'
            }
        }
    ]
    
    print("\n" + "=" * 80)
    print("CASE-BY-CASE COMPARISON")
    print("=" * 80)
    
    for i, data in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Data: {str(data)[:60]}...")
        
        comparison = analyzer.compare_equivalent_structures(data)
        comp = comparison['comparison']
        
        print(f"  JSON (pretty):  {comp['json_pretty_tokens']:3d} tokens")
        print(f"  JSON (compact): {comp['json_compact_tokens']:3d} tokens")
        print(f"  YAML (block):    {comp['yaml_block_tokens']:3d} tokens")
        print(f"  YAML (flow):     {comp['yaml_flow_tokens']:3d} tokens")
        
        if comp['yaml_block_tokens'] > comp['json_pretty_tokens']:
            diff = comp['yaml_block_tokens'] - comp['json_pretty_tokens']
            pct = comp['token_difference_pct']
            print(f"  → YAML uses {diff:+d} tokens ({pct:+.1f}%) more than JSON")
        else:
            diff = comp['json_pretty_tokens'] - comp['yaml_block_tokens']
            pct = -comp['token_difference_pct']
            print(f"  → JSON uses {diff:+d} tokens ({pct:+.1f}%) more than YAML")
    
    # Efficiency analysis
    print("\n" + "=" * 80)
    print("EFFICIENCY ANALYSIS (Averages)")
    print("=" * 80)
    
    efficiency = analyzer.analyze_token_efficiency(test_cases)
    avg = efficiency['averages']
    ratios = efficiency['ratios']
    
    print(f"\nAverage token counts across {efficiency['num_cases']} test cases:")
    print(f"  JSON (pretty):  {avg['json_pretty']:.1f} tokens")
    print(f"  JSON (compact): {avg['json_compact']:.1f} tokens")
    print(f"  YAML (block):   {avg['yaml_block']:.1f} tokens")
    print(f"  YAML (flow):    {avg['yaml_flow']:.1f} tokens")
    
    print(f"\nRatios:")
    print(f"  YAML block vs JSON pretty:  {ratios['yaml_block_vs_json_pretty']:.2f}x")
    print(f"  YAML block vs JSON compact: {ratios['yaml_block_vs_json_compact']:.2f}x")
    print(f"  JSON compact vs YAML block: {ratios['json_compact_vs_yaml_block']:.2f}x")
    
    # Token boundary analysis
    print("\n" + "=" * 80)
    print("TOKEN BOUNDARY ANALYSIS")
    print("=" * 80)
    
    sample_data = test_cases[0]
    json_text = json.dumps(sample_data, indent=2)
    yaml_text = yaml.dump(sample_data, default_flow_style=False)
    
    boundaries = analyzer.analyze_token_boundaries(json_text, yaml_text)
    
    print(f"\nJSON tokenization:")
    print(f"  Total tokens: {boundaries['json']['total_tokens']}")
    print(f"  Special tokens: {boundaries['json']['special_tokens']}")
    print(f"  Whitespace tokens: {boundaries['json']['whitespace_tokens']}")
    print(f"  Avg token length: {boundaries['json']['avg_token_length']:.2f} chars")
    print(f"  Sample tokens: {boundaries['json']['sample_tokens'][:10]}")
    
    print(f"\nYAML tokenization:")
    print(f"  Total tokens: {boundaries['yaml']['total_tokens']}")
    print(f"  Special tokens: {boundaries['yaml']['special_tokens']}")
    print(f"  Whitespace tokens: {boundaries['yaml']['whitespace_tokens']}")
    print(f"  Avg token length: {boundaries['yaml']['avg_token_length']:.2f} chars")
    print(f"  Sample tokens: {boundaries['yaml']['sample_tokens'][:10]}")
    
    print(f"\nDifferences:")
    diff = boundaries['differences']
    print(f"  Token count: {diff['token_count_diff']:+d}")
    print(f"  Special tokens: {diff['special_token_diff']:+d}")
    print(f"  Whitespace: {diff['whitespace_diff']:+d}")
    print(f"  Avg length: {diff['avg_length_diff']:+.2f} chars")
    
    # Generation cost
    print("\n" + "=" * 80)
    print("GENERATION COST ESTIMATE")
    print("=" * 80)
    
    cost = analyzer.measure_generation_cost(sample_data)
    
    print(f"\nJSON generation:")
    print(f"  Prompt tokens:  {cost['json']['prompt_tokens']:3d}")
    print(f"  Output tokens:   {cost['json']['output_tokens']:3d}")
    print(f"  Total tokens:   {cost['json']['total_tokens']:3d}")
    
    print(f"\nYAML generation:")
    print(f"  Prompt tokens:  {cost['yaml']['prompt_tokens']:3d}")
    print(f"  Output tokens:   {cost['yaml']['output_tokens']:3d}")
    print(f"  Total tokens:   {cost['yaml']['total_tokens']:3d}")
    
    comp = cost['comparison']
    print(f"\nComparison:")
    print(f"  Output token difference: {comp['output_token_diff']:+d}")
    print(f"  Output token ratio: {comp['output_token_ratio']:.2f}x")
    print(f"  Total token difference: {comp['total_token_diff']:+d}")
    print(f"  Total token ratio: {comp['total_token_ratio']:.2f}x")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if avg['yaml_block'] > avg['json_pretty']:
        print(f"\nYAML typically uses {avg['yaml_block'] - avg['json_pretty']:.1f} more tokens")
        print(f"than JSON (pretty) for equivalent structures.")
        print(f"This is a {((avg['yaml_block'] - avg['json_pretty']) / avg['json_pretty'] * 100):.1f}% increase.")
    else:
        print(f"\nJSON typically uses {avg['json_pretty'] - avg['yaml_block']:.1f} more tokens")
        print(f"than YAML for equivalent structures.")
    
    print(f"\nKey factors:")
    print(f"  - JSON requires quotes around keys and strings (more tokens)")
    print(f"  - YAML uses indentation (whitespace tokens)")
    print(f"  - YAML allows unquoted strings (fewer tokens)")
    print(f"  - Tokenization boundaries differ (affects token count)")


if __name__ == "__main__":
    run_token_count_analysis()

