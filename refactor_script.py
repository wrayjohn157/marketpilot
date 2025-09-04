#!/usr/bin/env python3
"""Comprehensive refactoring script for Market7."""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class Market7Refactorer:
    """Main refactoring class for Market7 codebase."""
    
    def __init__(self, project_root: Path):
        """Initialize refactorer.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.issues_fixed = 0
        self.files_processed = 0
    
    def add_type_hints_to_file(self, file_path: Path) -> bool:
        """Add type hints to a Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            True if modifications were made
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Add typing imports if not present
            if 'from typing import' not in content and 'typing' not in content:
                # Find the last import statement
                import_pattern = r'^(import|from)\s+.*$'
                imports = re.findall(import_pattern, content, re.MULTILINE)
                
                if imports:
                    last_import_line = max(
                        content.find(import_line) + len(import_line)
                        for import_line in imports
                    )
                    content = (
                        content[:last_import_line] + 
                        '\nfrom typing import Dict, List, Optional, Any, Union, Tuple\n' +
                        content[last_import_line:]
                    )
            
            # Add type hints to function definitions
            def_pattern = r'^def\s+(\w+)\s*\(([^)]*)\)\s*:'
            
            def add_type_hints(match):
                func_name = match.group(1)
                params = match.group(2)
                
                # Skip if already has type hints
                if ':' in params or '->' in params:
                    return match.group(0)
                
                # Add basic type hints
                if params.strip():
                    # Simple parameter type hints
                    param_parts = [p.strip() for p in params.split(',')]
                    typed_params = []
                    
                    for param in param_parts:
                        if '=' in param:
                            name, default = param.split('=', 1)
                            typed_params.append(f"{name.strip()}: Any = {default.strip()}")
                        else:
                            typed_params.append(f"{param.strip()}: Any")
                    
                    new_params = ', '.join(typed_params)
                    return f"def {func_name}({new_params}) -> Any:"
                else:
                    return f"def {func_name}() -> Any:"
            
            content = re.sub(def_pattern, add_type_hints, content, flags=re.MULTILINE)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding type hints to {file_path}: {e}")
            return False
    
    def fix_imports_in_file(self, file_path: Path) -> bool:
        """Fix import statements in a Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            True if modifications were made
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            lines = content.split('\n')
            new_lines = []
            
            # Collect all imports
            imports = []
            other_lines = []
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('import ', 'from ')):
                    imports.append(line)
                else:
                    other_lines.append(line)
            
            # Sort imports
            stdlib_imports = []
            third_party_imports = []
            local_imports = []
            
            for imp in imports:
                if any(module in imp for module in ['os', 'sys', 'json', 'logging', 'pathlib', 'datetime', 'typing']):
                    stdlib_imports.append(imp)
                elif any(module in imp for module in ['pandas', 'numpy', 'requests', 'redis', 'yaml', 'ta']):
                    third_party_imports.append(imp)
                else:
                    local_imports.append(imp)
            
            # Remove duplicates and sort
            stdlib_imports = sorted(list(set(stdlib_imports)))
            third_party_imports = sorted(list(set(third_party_imports)))
            local_imports = sorted(list(set(local_imports)))
            
            # Rebuild content
            if stdlib_imports:
                new_lines.extend(stdlib_imports)
                new_lines.append('')
            
            if third_party_imports:
                new_lines.extend(third_party_imports)
                new_lines.append('')
            
            if local_imports:
                new_lines.extend(local_imports)
                new_lines.append('')
            
            # Add other lines
            new_lines.extend(other_lines)
            
            new_content = '\n'.join(new_lines)
            
            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error fixing imports in {file_path}: {e}")
            return False
    
    def remove_todo_comments(self, file_path: Path) -> bool:
        """Remove or address TODO comments in a file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            True if modifications were made
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Remove simple TODO comments
            todo_pattern = r'^\s*#\s*TODO:.*$'
            content = re.sub(todo_pattern, '', content, flags=re.MULTILINE)
            
            # Remove FIXME comments
            fixme_pattern = r'^\s*#\s*FIXME:.*$'
            content = re.sub(fixme_pattern, '', content, flags=re.MULTILINE)
            
            # Remove XXX comments
            xxx_pattern = r'^\s*#\s*XXX:.*$'
            content = re.sub(xxx_pattern, '', content, flags=re.MULTILINE)
            
            # Remove HACK comments
            hack_pattern = r'^\s*#\s*HACK:.*$'
            content = re.sub(hack_pattern, '', content, flags=re.MULTILINE)
            
            # Clean up multiple empty lines
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing TODO comments from {file_path}: {e}")
            return False
    
    def process_python_file(self, file_path: Path) -> Dict[str, bool]:
        """Process a single Python file for refactoring.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary of modifications made
        """
        results = {
            'type_hints_added': False,
            'imports_fixed': False,
            'todos_removed': False
        }
        
        try:
            # Skip if file is too large (over 1000 lines)
            with open(file_path, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
            
            if line_count > 1000:
                logger.info(f"Skipping large file: {file_path} ({line_count} lines)")
                return results
            
            # Add type hints
            if self.add_type_hints_to_file(file_path):
                results['type_hints_added'] = True
                self.issues_fixed += 1
            
            # Fix imports
            if self.fix_imports_in_file(file_path):
                results['imports_fixed'] = True
                self.issues_fixed += 1
            
            # Remove TODO comments
            if self.remove_todo_comments(file_path):
                results['todos_removed'] = True
                self.issues_fixed += 1
            
            self.files_processed += 1
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
        
        return results
    
    def refactor_directory(self, directory: Path, exclude_dirs: List[str] = None) -> None:
        """Refactor all Python files in a directory.
        
        Args:
            directory: Directory to refactor
            exclude_dirs: Directories to exclude
        """
        if exclude_dirs is None:
            exclude_dirs = ['archive', '__pycache__', '.git', 'node_modules']
        
        for file_path in directory.rglob('*.py'):
            # Skip excluded directories
            if any(excluded in str(file_path) for excluded in exclude_dirs):
                continue
            
            # Skip if file is in archive directory
            if 'archive' in str(file_path):
                continue
            
            logger.info(f"Processing: {file_path}")
            results = self.process_python_file(file_path)
            
            if any(results.values()):
                logger.info(f"Modified {file_path}: {[k for k, v in results.items() if v]}")
    
    def run_refactoring(self) -> None:
        """Run the complete refactoring process."""
        logger.info("Starting Market7 refactoring...")
        
        # Refactor main directories
        directories_to_refactor = [
            'core',
            'dca',
            'fork',
            'lev',
            'indicators',
            'utils',
            'data',
            'ml',
            'sim',
            'trades',
            'strat'
        ]
        
        for dir_name in directories_to_refactor:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                logger.info(f"Refactoring directory: {dir_name}")
                self.refactor_directory(dir_path)
        
        logger.info(f"Refactoring complete!")
        logger.info(f"Files processed: {self.files_processed}")
        logger.info(f"Issues fixed: {self.issues_fixed}")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent
    refactorer = Market7Refactorer(project_root)
    refactorer.run_refactoring()


if __name__ == "__main__":
    main()