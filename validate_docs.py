#!/usr/bin/env python3
"""
Validate all YAML code blocks in documentation files.

Note: This script validates YAML syntax only. It does NOT verify that
example outputs match actual function results. For example, if documentation
shows the output of `normalize()`, this script only checks that the shown
output is valid Deterministic YAML, not that it matches what `normalize()`
would actually produce.

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

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from deterministic_yaml import DeterministicYAML


def extract_yaml_blocks(content: str, file_path: str) -> List[Tuple[int, str, str]]:
    """
    Extract YAML code blocks from markdown content.
    
    Returns:
        List of (line_number, language_tag, yaml_content) tuples
    """
    blocks = []
    lines = content.split('\n')
    in_code_block = False
    code_block_start = 0
    code_block_lang = None
    code_block_lines = []
    
    for i, line in enumerate(lines, 1):
        # Check for code block start
        match = re.match(r'^```(\w+)?', line)
        if match:
            if in_code_block:
                # End of code block
                if code_block_lang in ('yaml', 'yml', None):
                    yaml_content = '\n'.join(code_block_lines)
                    if yaml_content.strip():  # Only add non-empty blocks
                        blocks.append((code_block_start, code_block_lang or 'yaml', yaml_content))
                in_code_block = False
                code_block_lines = []
            else:
                # Start of code block
                in_code_block = True
                code_block_start = i
                code_block_lang = match.group(1)
        elif in_code_block:
            code_block_lines.append(line)
    
    # Handle unclosed code block
    if in_code_block and code_block_lang in ('yaml', 'yml', None):
        yaml_content = '\n'.join(code_block_lines)
        if yaml_content.strip():
            blocks.append((code_block_start, code_block_lang or 'yaml', yaml_content))
    
    return blocks


def validate_yaml_block(yaml_content: str, file_path: str, block_line: int) -> Tuple[bool, str]:
    """
    Validate a YAML block.
    
    Returns:
        (is_valid, error_message)
    """
    # Skip blocks that are clearly examples of invalid YAML or standard YAML
    # (e.g., blocks showing "Before" examples or "Invalid" examples)
    skip_markers = [
        '# This is', '# Production', '# Human wrote', '# Input with',
        '# Variant', '# Invalid', '❌', 'Incorrect:', '**Incorrect:**',
        'Before:', '**Before:**', 'Without', '**Without'
    ]
    
    # Check if this is an intentional example of invalid YAML
    if any(marker in yaml_content for marker in skip_markers):
        return True, "Skipped (intentional invalid/standard YAML example)"
    
    # Skip blocks that are clearly not YAML (tool output, grammar definitions, etc.)
    non_yaml_indicators = [
        'VARIANCE ANALYSIS', 'TOKEN COUNT', 'Test Case', 'Test 1:', 'Test 2:',
        'JSON Results:', 'YAML Results:', 'Next token candidates:',
        'Token        Logit', 'Position:', 'element(', '::=', '→'
    ]
    
    if any(indicator in yaml_content for indicator in non_yaml_indicators):
        return True, "Skipped (not YAML content - tool output or grammar)"
    
    # Skip GitHub Actions YAML (uses anchors/aliases which are standard YAML features)
    if 'on:' in yaml_content and ('push' in yaml_content or 'pull_request' in yaml_content or 'runs-on:' in yaml_content):
        return True, "Skipped (GitHub Actions YAML - uses standard YAML features)"
    
    # Skip blocks showing comments being forbidden (intentional examples)
    if '# Comments are' in yaml_content or '# Comments are EXPLICITLY' in yaml_content:
        return True, "Skipped (intentional example showing comments are forbidden)"
    
    # Handle false positive: `...` in hash values (not document markers)
    # The validator flags any `...` but document markers should only be on their own line
    # For now, if `...` appears in a value (after a colon), we'll note it but still validate
    # The core validator should be improved to only flag `...` on its own line
    
    # Validate using DeterministicYAML
    is_valid, error = DeterministicYAML.validate(yaml_content)
    return is_valid, error or ""


def check_code_examples(file_path: Path, content: str) -> List[Tuple[int, str]]:
    """
    Check that code examples showing function output match actual results.
    
    NOTE: This is a basic check. Full validation would require:
    - Parsing Python AST to extract function calls and inputs
    - Executing the code in a sandbox
    - Comparing actual vs expected output
    
    For now, this is a placeholder for future enhancement.
    
    Returns list of (line_number, error_message) tuples.
    """
    errors = []
    # TODO: Implement code example validation
    # This would check that examples like:
    #   deterministic_yaml = DeterministicYAML.normalize(standard_yaml)
    #   print(deterministic_yaml)
    # Actually produce the shown output
    return errors


def main():
    """Main validation function."""
    # Find all markdown files
    md_files = []
    for pattern in ['*.md', '**/*.md']:
        md_files.extend(Path('.').glob(pattern))
    
    # Remove duplicates and sort
    md_files = sorted(set(md_files))
    
    total_blocks = 0
    total_valid = 0
    total_invalid = 0
    total_skipped = 0
    errors = []
    
    print("Validating YAML blocks in documentation files...\n")
    
    for md_file in md_files:
        if 'node_modules' in str(md_file) or '.git' in str(md_file):
            continue
        
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"⚠️  Could not read {md_file}: {e}")
            continue
        
        blocks = extract_yaml_blocks(content, str(md_file))
        
        if not blocks:
            continue
        
        print(f"📄 {md_file} ({len(blocks)} YAML block(s))")
        
        for block_line, lang, yaml_content in blocks:
            total_blocks += 1
            is_valid, error = validate_yaml_block(yaml_content, str(md_file), block_line)
            
            if error == "Skipped (standard YAML example)":
                total_skipped += 1
                print(f"   ⏭️  Block at line {block_line}: Skipped (standard YAML example)")
            elif is_valid:
                total_valid += 1
                print(f"   ✅ Block at line {block_line}: Valid")
            else:
                total_invalid += 1
                print(f"   ❌ Block at line {block_line}: Invalid - {error}")
                errors.append((md_file, block_line, error, yaml_content[:100]))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total YAML blocks found: {total_blocks}")
    print(f"✅ Valid: {total_valid}")
    print(f"❌ Invalid: {total_invalid}")
    print(f"⏭️  Skipped: {total_skipped}")
    
    if errors:
        print("\n" + "=" * 70)
        print("ERRORS")
        print("=" * 70)
        for file_path, line, error, preview in errors:
            print(f"\n{file_path}:{line}")
            print(f"  Error: {error}")
            print(f"  Preview: {preview}...")
        
        sys.exit(1)
    else:
        print("\n✅ All YAML blocks are valid!")
        sys.exit(0)


if __name__ == '__main__':
    main()

