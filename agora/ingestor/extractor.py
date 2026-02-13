"""
Universal Code Ingestor - AST-Based Code Extractor

Extracts function metadata from Python source files using AST.
Handles syntax errors gracefully and generates dependency graphs.
"""

import ast
import os
import logging
from pathlib import Path
from typing import List, Set, Optional
from agora.ingestor.models import FunctionMetadata, ParameterInfo

logger = logging.getLogger(__name__)


class CodeExtractor:
    """
    Extract function metadata from Python source code using AST.
    
    Features:
    - Extracts functions and methods
    - Builds dependency graph (internal function calls)
    - Generates intent summaries for undocumented code
    - Error-tolerant parsing
    """
    
    def __init__(
        self,
        project_root: str,
        exclude_patterns: Optional[List[str]] = None
    ):
        """
        Initialize code extractor.
        
        Args:
            project_root: Root directory of the project
            exclude_patterns: Patterns to exclude (e.g., ['test_*', '__pycache__'])
        """
        self.project_root = Path(project_root).resolve()
        self.exclude_patterns = exclude_patterns or [
            'test_*',
            '*_test.py',
            '__pycache__',
            '.git',
            '.venv',
            'venv',
            'node_modules',
            'migrations',
            '.pytest_cache'
        ]
        self.errors = []
    
    def should_exclude(self, path: Path) -> bool:
        """Check if path matches exclusion patterns."""
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False
    
    def scan_directory(self, directory: Optional[str] = None) -> List[FunctionMetadata]:
        """
        Recursively scan directory for Python files and extract functions.
        
        Args:
            directory: Directory to scan (defaults to project_root)
            
        Returns:
            List of extracted function metadata
        """
        scan_dir = Path(directory) if directory else self.project_root
        all_functions = []
        
        logger.info(f"Scanning directory: {scan_dir}")
        
        for py_file in scan_dir.rglob("*.py"):
            if self.should_exclude(py_file):
                continue
            
            try:
                functions = self.extract_from_file(py_file)
                all_functions.extend(functions)
                logger.debug(f"Extracted {len(functions)} functions from {py_file}")
            except Exception as e:
                self.errors.append((str(py_file), str(e)))
                logger.warning(f"Error processing {py_file}: {e}")
        
        logger.info(f"Extracted {len(all_functions)} total functions")
        if self.errors:
            logger.warning(f"Encountered {len(self.errors)} errors during extraction")
        
        return all_functions
    
    def extract_from_file(self, file_path: Path) -> List[FunctionMetadata]:
        """
        Extract all functions from a single Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            List of function metadata
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse AST
        try:
            tree = ast.parse(source_code, filename=str(file_path))
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return []
        
        # Get relative path
        try:
            rel_path = file_path.relative_to(self.project_root)
        except ValueError:
            # File is outside project root
            rel_path = file_path
        
        # Extract functions
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                try:
                    func_meta = self._extract_function(node, source_code, str(rel_path))
                    if func_meta:
                        functions.append(func_meta)
                except Exception as e:
                    logger.warning(f"Error extracting function {node.name} from {file_path}: {e}")
        
        return functions
    
    def _extract_function(
        self,
        node: ast.FunctionDef,
        source_code: str,
        file_path: str
    ) -> Optional[FunctionMetadata]:
        """Extract metadata from a function AST node."""
        
        # Get source code for this function
        try:
            func_source = ast.get_source_segment(source_code, node)
        except:
            func_source = ""
        
        # Get docstring
        docstring = ast.get_docstring(node)
        
        # Generate intent summary if no docstring
        intent_summary = None
        if not docstring:
            intent_summary = self._generate_intent_summary(node)
        
        # Extract parameters
        parameters = self._extract_parameters(node)
        
        # Extract return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)
        
        # Build signature
        signature = self._build_signature(node)
        
        # Extract dependencies (internal function calls)
        dependencies = self._extract_dependencies(node)
        
        return FunctionMetadata(
            function_name=node.name,
            file_path=file_path,
            language="python",
            signature=signature,
            source_code=func_source or "",
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=docstring,
            intent_summary=intent_summary,
            parameters=parameters,
            return_type=return_type,
            dependencies=dependencies
        )
    
    def _extract_parameters(self, node: ast.FunctionDef) -> List[ParameterInfo]:
        """Extract parameter information from function node."""
        parameters = []
        args = node.args
        
        # Regular arguments
        for i, arg in enumerate(args.args):
            # Skip 'self' and 'cls'
            if arg.arg in ('self', 'cls'):
                continue
            
            type_hint = None
            if arg.annotation:
                type_hint = ast.unparse(arg.annotation)
            
            # Check for default value
            default = None
            is_required = True
            defaults_offset = len(args.args) - len(args.defaults)
            if i >= defaults_offset:
                default_node = args.defaults[i - defaults_offset]
                default = ast.unparse(default_node)
                is_required = False
            
            parameters.append(ParameterInfo(
                name=arg.arg,
                type_hint=type_hint,
                default=default,
                is_required=is_required
            ))
        
        # *args
        if args.vararg:
            parameters.append(ParameterInfo(
                name=f"*{args.vararg.arg}",
                type_hint=ast.unparse(args.vararg.annotation) if args.vararg.annotation else None,
                is_required=False
            ))
        
        # **kwargs
        if args.kwarg:
            parameters.append(ParameterInfo(
                name=f"**{args.kwarg.arg}",
                type_hint=ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None,
                is_required=False
            ))
        
        return parameters
    
    def _build_signature(self, node: ast.FunctionDef) -> str:
        """Build function signature string."""
        params = []
        args = node.args
        
        # Regular args
        for i, arg in enumerate(args.args):
            param_str = arg.arg
            if arg.annotation:
                param_str += f": {ast.unparse(arg.annotation)}"
            
            # Add default
            defaults_offset = len(args.args) - len(args.defaults)
            if i >= defaults_offset:
                default = ast.unparse(args.defaults[i - defaults_offset])
                param_str += f" = {default}"
            
            params.append(param_str)
        
        # *args
        if args.vararg:
            vararg_str = f"*{args.vararg.arg}"
            if args.vararg.annotation:
                vararg_str += f": {ast.unparse(args.vararg.annotation)}"
            params.append(vararg_str)
        
        # **kwargs
        if args.kwarg:
            kwarg_str = f"**{args.kwarg.arg}"
            if args.kwarg.annotation:
                kwarg_str += f": {ast.unparse(args.kwarg.annotation)}"
            params.append(kwarg_str)
        
        # Return type
        return_str = ""
        if node.returns:
            return_str = f" -> {ast.unparse(node.returns)}"
        
        return f"{node.name}({', '.join(params)}){return_str}"
    
    def _extract_dependencies(self, node: ast.FunctionDef) -> List[str]:
        """
        Extract internal function calls (dependencies).
        
        Captures full attribute chains for better context.
        Examples:
        - db.users.get() → "db.users.get"
        - validate_email() → "validate_email"
        - self.process() → "self.process"
        
        Returns list of function/method calls within this function.
        """
        dependencies = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Get full function/method call path
                call_path = self._get_call_path(child.func)
                if call_path:
                    dependencies.add(call_path)
        
        return sorted(list(dependencies))
    
    def _get_call_path(self, node: ast.expr) -> Optional[str]:
        """
        Extract full call path from an AST node.
        
        Examples:
        - ast.Name('func') → "func"
        - ast.Attribute(Name('obj'), 'method') → "obj.method"
        - ast.Attribute(Attribute(Name('db'), 'users'), 'get') → "db.users.get"
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Recursively build the attribute chain
            value_path = self._get_call_path(node.value)
            if value_path:
                return f"{value_path}.{node.attr}"
            else:
                return node.attr
        else:
            # For complex expressions, try to unparse
            try:
                return ast.unparse(node)
            except:
                return None
    
    def _generate_intent_summary(self, node: ast.FunctionDef) -> str:
        """
        Generate a 1-sentence intent summary for undocumented functions.
        
        Uses heuristics based on function name and structure.
        """
        name = node.name
        
        # Common patterns
        if name.startswith('get_'):
            return f"Retrieves {name[4:].replace('_', ' ')}"
        elif name.startswith('set_'):
            return f"Sets {name[4:].replace('_', ' ')}"
        elif name.startswith('create_'):
            return f"Creates {name[7:].replace('_', ' ')}"
        elif name.startswith('delete_'):
            return f"Deletes {name[7:].replace('_', ' ')}"
        elif name.startswith('update_'):
            return f"Updates {name[7:].replace('_', ' ')}"
        elif name.startswith('is_') or name.startswith('has_'):
            return f"Checks if {name[3:].replace('_', ' ')}"
        elif name.startswith('validate_'):
            return f"Validates {name[9:].replace('_', ' ')}"
        elif name.startswith('process_'):
            return f"Processes {name[8:].replace('_', ' ')}"
        elif name.startswith('handle_'):
            return f"Handles {name[7:].replace('_', ' ')}"
        elif name == '__init__':
            return "Initializes the object"
        else:
            # Generic summary
            return f"Function {name.replace('_', ' ')}"
    
    def get_errors(self) -> List[tuple[str, str]]:
        """Get list of (file_path, error_message) tuples."""
        return self.errors
