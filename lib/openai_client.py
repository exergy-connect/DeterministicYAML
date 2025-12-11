"""
OpenAI API client wrapper for quantifying JSON vs YAML differences.

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

import openai
from typing import List, Dict, Tuple, Optional
import os


class OpenAIClient:
    """Wrapper for OpenAI API with logprob support."""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        """
        Initialize OpenAI client.
        
        Args:
            model: Model name (e.g., "gpt-4o-mini", "gpt-3.5-turbo")
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.model = model
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key.")
        self.client = openai.OpenAI(api_key=api_key)
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 1.0,
        logprobs: Optional[int] = None,
        return_logprobs: bool = False,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        """
        Generate text with optional logprobs.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            logprobs: Number of top logprobs to return (if supported)
            return_logprobs: Whether to return logprobs dict
            **kwargs: Additional parameters
        
        Returns:
            (generated_text, logprobs_dict)
        """
        try:
            # For chat models, use chat completion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                **kwargs
            )
            
            text = response.choices[0].message.content
            
            # Extract logprobs if available
            logprobs_dict = None
            if return_logprobs and hasattr(response.choices[0], 'logprobs'):
                # Note: Chat models may not support logprobs in all versions
                logprobs_dict = self._extract_logprobs(response.choices[0].logprobs)
            
            return text, logprobs_dict
            
        except Exception as e:
            print(f"Error generating text: {e}")
            return "", None
    
    def _extract_logprobs(self, logprobs_obj) -> Optional[Dict]:
        """Extract logprobs from response object."""
        if not logprobs_obj:
            return None
        
        # Structure: {position: {token: logprob}}
        result = {}
        
        if hasattr(logprobs_obj, 'content'):
            for i, token_logprob in enumerate(logprobs_obj.content):
                if hasattr(token_logprob, 'top_logprobs'):
                    result[i] = {
                        item.token: item.logprob
                        for item in token_logprob.top_logprobs
                    }
        
        return result
    
    def get_next_token_probs(
        self,
        prompt: str,
        top_k: int = 10
    ) -> Dict[str, float]:
        """
        Get probability distribution for next token.
        
        Args:
            prompt: Input prompt
            top_k: Number of top tokens to return
        
        Returns:
            Dict mapping token -> probability
        """
        # Use completion API with logprobs for better token-level access
        try:
            response = self.client.completions.create(
                model=self.model,
                prompt=prompt,
                max_tokens=1,
                logprobs=top_k,
                temperature=0.0  # Deterministic for probability measurement
            )
            
            if response.choices and response.choices[0].logprobs:
                logprobs = response.choices[0].logprobs
                if logprobs.top_logprobs:
                    # Convert logprobs to probabilities
                    import numpy as np
                    probs = {}
                    for item in logprobs.top_logprobs[0]:
                        probs[item.token] = np.exp(item.logprob)
                    return probs
            
        except Exception as e:
            # Fallback to chat API if completion API not available
            print(f"Completion API error: {e}, trying chat API...")
            text, _ = self.generate(prompt, max_tokens=1, temperature=0.0)
            return {text: 1.0} if text else {}
        
        return {}


def example_usage():
    """Example of using OpenAI client."""
    import os
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY environment variable to run this example.")
        return
    
    client = OpenAIClient(model="gpt-4o-mini", api_key=api_key)
    
    # Compare next-token probabilities
    json_prompt = "Generate a JSON object with a 'name' key:\n{"
    yaml_prompt = "Generate a YAML mapping with a 'name' key:\nname"
    
    print("JSON next-token probabilities (after '{'):")
    json_probs = client.get_next_token_probs(json_prompt, top_k=10)
    for token, prob in sorted(json_probs.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {repr(token):20s} {prob:.4f}")
    
    print("\nYAML next-token probabilities (after 'name'):")
    yaml_probs = client.get_next_token_probs(yaml_prompt, top_k=10)
    for token, prob in sorted(yaml_probs.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {repr(token):20s} {prob:.4f}")


if __name__ == "__main__":
    example_usage()

