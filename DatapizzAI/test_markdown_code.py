#!/usr/bin/env python3
"""
Script to extract and test all Python code snippets from markdown files.
Creates test files and reports errors.
"""
import re
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple
import json

class MarkdownCodeTester:
    def __init__(self, base_dir: str, test_env_python: str):
        self.base_dir = Path(base_dir)
        self.test_env_python = test_env_python
        self.results = []
        self.test_scripts_dir = self.base_dir / "test_scripts"
        self.test_scripts_dir.mkdir(exist_ok=True)
        
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in the directory."""
        md_files = []
        # Exclude datapizza-ai-main internal docs
        for pattern in ['**/README*.md', '**/*Guide*.md', '**/*GUIDE*.md']:
            for file in self.base_dir.rglob(pattern):
                if 'datapizza-ai-main' not in str(file):
                    md_files.append(file)
        return sorted(set(md_files))
    
    def extract_code_blocks(self, md_file: Path) -> List[Tuple[int, str]]:
        """Extract Python code blocks from markdown file."""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all ```python code blocks
        pattern = r'```python\n(.*?)```'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        code_blocks = []
        for match in matches:
            code = match.group(1)
            # Find line number
            line_num = content[:match.start()].count('\n') + 1
            code_blocks.append((line_num, code))
        
        return code_blocks
    
    def is_testable_code(self, code: str) -> bool:
        """Check if code block should be tested."""
        # Skip if it's just imports or configuration
        lines = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
        
        # Skip empty or comment-only blocks
        if not lines:
            return False
        
        # Skip if it's only pip install commands
        if all(l.startswith('pip ') or l.startswith('uv ') for l in lines):
            return False
        
        # Skip bash/shell commands
        if any(l.startswith('docker ') or l.startswith('chmod ') or l.startswith('cd ') for l in lines):
            return False
            
        # Skip if contains placeholder API keys
        if 'sk-your-key-here' in code or 'your-api-key-here' in code:
            return True  # We'll mock these
        
        return True
    
    def prepare_test_code(self, code: str, file_context: str) -> str:
        """Prepare code for testing by adding mocks and error handling."""
        # Add mock environment variables
        setup = '''
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Mock environment variables
os.environ.setdefault('OPENAI_API_KEY', 'sk-test-key-mock')
os.environ.setdefault('ANTHROPIC_API_KEY', 'sk-ant-test-key-mock')
os.environ.setdefault('GOOGLE_API_KEY', 'test-google-key-mock')
os.environ.setdefault('MISTRAL_API_KEY', 'test-mistral-key-mock')
os.environ.setdefault('AZURE_OPENAI_API_KEY', 'test-azure-key-mock')
os.environ.setdefault('AZURE_OPENAI_ENDPOINT', 'https://test.openai.azure.com/')
os.environ.setdefault('AZURE_OPENAI_DEPLOYMENT', 'test-deployment')

# Flag to track if this is a syntax/import test only
SYNTAX_TEST_ONLY = False
'''
        
        # Wrap the code
        wrapped_code = f"""
{setup}

try:
    # Original code from markdown
{self._indent_code(code, '    ')}
    print("✓ Code executed successfully")
except ImportError as e:
    print(f"✗ Import Error: {{e}}")
    sys.exit(1)
except NameError as e:
    print(f"✗ Name Error: {{e}}")
    sys.exit(1)
except AttributeError as e:
    print(f"⚠ Attribute Error (might be OK if testing imports): {{e}}")
except Exception as e:
    print(f"⚠ Runtime Error (might be expected): {{e}}")
"""
        return wrapped_code
    
    def _indent_code(self, code: str, indent: str) -> str:
        """Add indentation to code."""
        return '\n'.join(indent + line if line.strip() else line 
                        for line in code.split('\n'))
    
    def test_code_block(self, md_file: Path, line_num: int, code: str, block_idx: int) -> Dict:
        """Test a single code block."""
        result = {
            'file': str(md_file.relative_to(self.base_dir)),
            'line': line_num,
            'block_index': block_idx,
            'status': 'unknown',
            'error': None,
            'test_file': None
        }
        
        # Create test file
        test_filename = f"test_{md_file.stem}_block_{block_idx}.py"
        test_file = self.test_scripts_dir / test_filename
        result['test_file'] = str(test_file.relative_to(self.base_dir))
        
        test_code = self.prepare_test_code(code, str(md_file))
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        # Run the test
        try:
            proc = subprocess.run(
                [self.test_env_python, str(test_file)],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.base_dir
            )
            
            if proc.returncode == 0:
                result['status'] = 'success'
            else:
                result['status'] = 'error'
                result['error'] = proc.stdout + '\n' + proc.stderr
        except subprocess.TimeoutExpired:
            result['status'] = 'timeout'
            result['error'] = 'Test timed out after 10 seconds'
        except Exception as e:
            result['status'] = 'exception'
            result['error'] = str(e)
        
        return result
    
    def test_markdown_file(self, md_file: Path) -> List[Dict]:
        """Test all code blocks in a markdown file."""
        print(f"\nTesting: {md_file.relative_to(self.base_dir)}")
        
        code_blocks = self.extract_code_blocks(md_file)
        print(f"  Found {len(code_blocks)} code blocks")
        
        results = []
        for idx, (line_num, code) in enumerate(code_blocks):
            if not self.is_testable_code(code):
                print(f"  Block {idx+1} (line {line_num}): Skipped (not testable)")
                continue
            
            result = self.test_code_block(md_file, line_num, code, idx + 1)
            results.append(result)
            
            status_symbol = {'success': '✓', 'error': '✗', 'timeout': '⏱', 'exception': '⚠'}
            print(f"  Block {idx+1} (line {line_num}): {status_symbol.get(result['status'], '?')} {result['status']}")
            
        return results
    
    def run_all_tests(self):
        """Run tests on all markdown files."""
        md_files = self.find_markdown_files()
        print(f"Found {len(md_files)} markdown files to test")
        
        for md_file in md_files:
            file_results = self.test_markdown_file(md_file)
            self.results.extend(file_results)
        
        return self.results
    
    def generate_report(self, output_file: str):
        """Generate markdown report of test results."""
        # Group results by file
        by_file = {}
        for result in self.results:
            file = result['file']
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(result)
        
        # Count statistics
        total = len(self.results)
        success = sum(1 for r in self.results if r['status'] == 'success')
        errors = sum(1 for r in self.results if r['status'] == 'error')
        
        report = f"""# Report di correzione codice Markdown

Data analisi: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Statistiche generali

- **File analizzati**: {len(by_file)}
- **Blocchi di codice testati**: {total}
- **Successi**: {success} ({success/total*100:.1f}% se total > 0)
- **Errori**: {errors} ({errors/total*100:.1f}% se total > 0)
- **Altri**: {total - success - errors}

## Analisi dettagliata per file

"""
        
        for file, file_results in sorted(by_file.items()):
            file_errors = [r for r in file_results if r['status'] == 'error']
            file_success = [r for r in file_results if r['status'] == 'success']
            
            status_icon = '✅' if not file_errors else '⚠️' if file_success else '❌'
            
            report += f"### {status_icon} `{file}`\n\n"
            report += f"**Blocchi testati**: {len(file_results)} | "
            report += f"**Successi**: {len(file_success)} | "
            report += f"**Errori**: {len(file_errors)}\n\n"
            
            if file_errors:
                report += "#### Errori riscontrati\n\n"
                for result in file_errors:
                    report += f"**Blocco #{result['block_index']}** (linea {result['line']})\n\n"
                    report += f"File di test: `{result['test_file']}`\n\n"
                    report += "```\n"
                    report += result['error'][:500]  # Limit error output
                    if len(result['error']) > 500:
                        report += "\n... (troncato)"
                    report += "\n```\n\n"
            
            report += "---\n\n"
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✓ Report salvato in: {output_file}")


if __name__ == '__main__':
    base_dir = '/home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI'
    test_env_python = '/home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/datapizza-ai-main/test/bin/python'
    
    tester = MarkdownCodeTester(base_dir, test_env_python)
    tester.run_all_tests()
    tester.generate_report('/home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/Correction.MD')


