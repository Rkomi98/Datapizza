"""
Syntax-only validation script for video code examples.
This checks Python syntax and basic structure without making API calls.
"""

import ast
import sys
from pathlib import Path

def validate_python_syntax(code: str, context: str) -> tuple[bool, str]:
    """Validate Python code syntax."""
    try:
        ast.parse(code)
        return True, f"✓ {context}: Syntax valid"
    except SyntaxError as e:
        return False, f"✗ {context}: Syntax error at line {e.lineno}: {e.msg}"

def extract_code_blocks(md_file: Path) -> list[tuple[str, str]]:
    """Extract Python code blocks from markdown file."""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    code_blocks = []
    in_code_block = False
    current_code = []
    block_num = 0
    
    for line in content.split('\n'):
        if line.strip().startswith('```python'):
            in_code_block = True
            block_num += 1
            current_code = []
        elif line.strip().startswith('```') and in_code_block:
            in_code_block = False
            if current_code:
                code = '\n'.join(current_code)
                code_blocks.append((f"Block {block_num}", code))
        elif in_code_block:
            current_code.append(line)
    
    return code_blocks

def validate_script(script_path: Path) -> tuple[int, int]:
    """Validate all code blocks in a script."""
    print(f"\n{'='*60}")
    print(f"Validating: {script_path.name}")
    print('='*60)
    
    if not script_path.exists():
        print(f"✗ File not found: {script_path}")
        return 0, 1
    
    code_blocks = extract_code_blocks(script_path)
    
    if not code_blocks:
        print("⚠ No Python code blocks found")
        return 0, 0
    
    passed = 0
    failed = 0
    
    for context, code in code_blocks:
        success, message = validate_python_syntax(code, context)
        print(message)
        if success:
            passed += 1
        else:
            failed += 1
    
    return passed, failed

def main():
    """Validate all video scripts."""
    print("="*60)
    print("SYNTAX VALIDATION FOR VIDEO SCRIPTS")
    print("="*60)
    print("This checks Python syntax without running the code.")
    print("No API calls or dependencies required.\n")
    
    script_dir = Path(__file__).parent / "Scripts"
    
    scripts = [
        script_dir / "video_03_structured_multimodal.md",
        script_dir / "video_08_rag_implementation.md",
        script_dir / "video_09_pipelines_monitoring.md"
    ]
    
    total_passed = 0
    total_failed = 0
    
    for script in scripts:
        passed, failed = validate_script(script)
        total_passed += passed
        total_failed += failed
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Total blocks validated: {total_passed + total_failed}")
    print(f"✓ Passed: {total_passed}")
    print(f"✗ Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 All syntax checks passed!")
        print("You're ready to test with actual API calls.")
        return 0
    else:
        print(f"\n⚠ {total_failed} syntax error(s) found.")
        print("Fix these before recording.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

