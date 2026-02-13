"""
CodebaseAnalyzer - Production-Ready AST-based Python Codebase Analysis

Analyzes Python codebases to discover functions, extract comprehensive metadata,
and identify patterns for auto-generating Agora nodes.

Features:
- Advanced import resolution
- Rich metadata extraction (docstrings, type hints, parameters)
- Error-tolerant parsing with fallback
- Internal dependency mapping
"""

import ast
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ParameterMetadata:
    """Metadata for a function parameter"""
    name: str
    type_hint: Optional[str] = None
    default_value: Optional[str] = None
    is_required: bool = True


@dataclass
class FunctionMetadata:
    """Comprehensive metadata for a discovered function"""
    name: str
    signature: str
    docstring: Optional[str]
    source_file: str
    module_path: str  # Python import path (e.g., "src.auth.utils")
    line_number: int
    is_async: bool
    parameters: List[ParameterMetadata]
    return_annotation: Optional[str]
    dependencies: List[str]  # Internal function calls
    external_imports: List[str]  # External modules used
    full_source: Optional[str] = None  # Full function source code
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FunctionMetadata':
        # Convert parameter dicts back to ParameterMetadata objects
        if 'parameters' in data and data['parameters']:
            data['parameters'] = [
                ParameterMetadata(**p) if isinstance(p, dict) else p
                for p in data['parameters']
            ]
        return cls(**data)


class CodebaseAnalyzer:
    """
    Production-ready Python codebase analyzer.
    
    Features:
    - Calculates correct Python import paths
    - Extracts full docstrings and type hints
    - Error-tolerant parsing (continues on syntax errors)
    - Maps internal function dependencies
    
    Example:
        >>> analyzer = CodebaseAnalyzer(project_root="./my_project")
        >>> functions = analyzer.analyze_directory("./my_project/src")
        >>> print(f"Found {len(functions)} functions")
        >>> for func in functions:
        ...     print(f"{func.module_path}.{func.name}")
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize analyzer.
        
        Args:
            project_root: Root directory of the project (for import path calculation)
                         If None, will be inferred from analyzed directory
        """
        self.project_root = Path(project_root) if project_root else None
        self.functions: List[FunctionMetadata] = []
        self.errors: List[Dict[str, str]] = []
        self.skip_patterns = [
            "test_",
            "_test.py",
            "tests/",
            "migrations/",
            "__pycache__",
            ".venv",
            "venv/",
            "node_modules/",
            ".git/",
        ]
        # Track all functions for dependency resolution
        self._all_function_names: Set[str] = set()
    
    def should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        path_str = str(file_path)
        return any(pattern in path_str for pattern in self.skip_patterns)
    
    def _calculate_module_path(self, file_path: Path) -> str:
        """
        Calculate Python import path from file path.
        
        Args:
            file_path: Absolute path to Python file
            
        Returns:
            Python module path (e.g., "src.auth.utils")
        """
        if not self.project_root:
            # Use file's parent directory as root
            relative_path = file_path.stem
        else:
            # Calculate relative to project root
            try:
                relative_path = file_path.relative_to(self.project_root)
            except ValueError:
                # File is outside project root, use file name only
                logger.warning(f"File {file_path} is outside project root {self.project_root}")
                # Just use the filename without path
                return file_path.stem
        
        # Convert path to module notation
        parts = list(relative_path.parts[:-1]) + [relative_path.stem]
        
        # Remove __init__ from path
        if parts and parts[-1] == '__init__':
            parts = parts[:-1]
        
        # Filter out empty parts
        parts = [p for p in parts if p]
        
        # Join with dots
        module_path = '.'.join(parts) if parts else file_path.stem
        
        return module_path
    
    def analyze_directory(
        self,
        path: str,
        extensions: Optional[List[str]] = None
    ) -> List[FunctionMetadata]:
        """
        Analyze all Python files in a directory.
        
        Args:
            path: Directory path to analyze
            extensions: File extensions to include (default: [".py"])
            
        Returns:
            List of FunctionMetadata for all discovered functions
        """
        if extensions is None:
            extensions = [".py"]
        
        self.functions = []
        self.errors = []
        self._all_function_names = set()
        root_path = Path(path).resolve()
        
        if not root_path.exists():
            raise ValueError(f"Path does not exist: {path}")
        
        # Set project root if not already set
        if not self.project_root:
            self.project_root = root_path
        
        # First pass: collect all function names
        logger.info(f"Scanning {root_path} for functions...")
        all_files = []
        for ext in extensions:
            for file_path in root_path.rglob(f"*{ext}"):
                if self.should_skip(file_path):
                    continue
                all_files.append(file_path)
        
        # Second pass: analyze files
        for file_path in all_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                error_msg = f"Unexpected error analyzing {file_path}: {e}"
                logger.error(error_msg)
                self.errors.append({
                    "file": str(file_path),
                    "error": str(e),
                    "type": "unexpected"
                })
        
        logger.info(f"Analysis complete: {len(self.functions)} functions, {len(self.errors)} errors")
        
        return self.functions
    
    def _analyze_file(self, file_path: Path):
        """
        Analyze a single Python file with error tolerance.
        
        Requirement 3: Error-Tolerant Parsing
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            self.errors.append({
                "file": str(file_path),
                "error": str(e),
                "type": "read_error"
            })
            return
        
        # Try to parse with error handling
        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}:{e.lineno} - {e.msg}")
            self.errors.append({
                "file": str(file_path),
                "error": f"Line {e.lineno}: {e.msg}",
                "type": "syntax_error"
            })
            return
        except Exception as e:
            logger.warning(f"Parse error in {file_path}: {e}")
            self.errors.append({
                "file": str(file_path),
                "error": str(e),
                "type": "parse_error"
            })
            return
        
        # Calculate module path
        module_path = self._calculate_module_path(file_path)
        
        # Extract imports
        external_imports = self._extract_imports(tree)
        
        # Find all function definitions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                try:
                    func_meta = self._extract_function(
                        node, file_path, module_path, source, external_imports
                    )
                    if func_meta:
                        self.functions.append(func_meta)
                        self._all_function_names.add(func_meta.name)
                except Exception as e:
                    logger.warning(f"Error extracting function {node.name} from {file_path}: {e}")
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all external imports from the AST"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_import = f"{module}.{alias.name}" if module else alias.name
                    imports.append(full_import)
        
        return imports
    
    def _extract_function(
        self,
        node: ast.FunctionDef,
        file_path: Path,
        module_path: str,
        source: str,
        external_imports: List[str]
    ) -> Optional[FunctionMetadata]:
        """
        Extract comprehensive metadata from a function definition.
        
        Requirement 2: Rich Metadata Persistence
        """
        
        # Skip private functions (starting with _) unless they're magic methods
        if node.name.startswith('_') and not node.name.startswith('__'):
            return None
        
        # Extract parameters with type hints
        parameters = self._extract_parameters(node)
        
        # Build signature
        param_strs = []
        for param in parameters:
            if param.type_hint:
                param_str = f"{param.name}: {param.type_hint}"
            else:
                param_str = param.name
            
            if param.default_value:
                param_str += f" = {param.default_value}"
            
            param_strs.append(param_str)
        
        signature = f"{node.name}({', '.join(param_strs)})"
        
        # Get return annotation
        return_annotation = None
        if node.returns:
            try:
                return_annotation = ast.unparse(node.returns)
            except:
                return_annotation = "<complex type>"
        
        # Get full docstring
        docstring = ast.get_docstring(node)
        
        # Extract full function source
        try:
            full_source = ast.get_source_segment(source, node)
        except:
            full_source = None
        
        # Find internal dependencies
        dependencies = self._find_internal_dependencies(node)
        
        return FunctionMetadata(
            name=node.name,
            signature=signature,
            docstring=docstring,
            source_file=str(file_path),
            module_path=module_path,
            line_number=node.lineno,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            parameters=parameters,
            return_annotation=return_annotation,
            dependencies=dependencies,
            external_imports=external_imports,
            full_source=full_source
        )
    
    def _extract_parameters(self, node: ast.FunctionDef) -> List[ParameterMetadata]:
        """
        Extract parameter metadata with type hints and defaults.
        
        Requirement 2: Rich Metadata Persistence
        """
        parameters = []
        args = node.args
        
        # Get defaults (they align with the end of the args list)
        defaults = [None] * (len(args.args) - len(args.defaults)) + list(args.defaults)
        
        for arg, default in zip(args.args, defaults):
            # Skip 'self' and 'cls'
            if arg.arg in ('self', 'cls'):
                continue
            
            # Get type hint
            type_hint = None
            if arg.annotation:
                try:
                    type_hint = ast.unparse(arg.annotation)
                except:
                    type_hint = "<complex type>"
            
            # Get default value
            default_value = None
            is_required = True
            if default is not None:
                try:
                    default_value = ast.unparse(default)
                    is_required = False
                except:
                    default_value = "<complex default>"
                    is_required = False
            
            parameters.append(ParameterMetadata(
                name=arg.arg,
                type_hint=type_hint,
                default_value=default_value,
                is_required=is_required
            ))
        
        return parameters
    
    def _find_internal_dependencies(self, node: ast.FunctionDef) -> List[str]:
        """
        Find internal function calls within a function.
        
        Requirement 4: Dependency Mapping
        """
        dependencies = set()
        
        for child in ast.walk(node):
            # Find function calls
            if isinstance(child, ast.Call):
                func_name = None
                
                if isinstance(child.func, ast.Name):
                    # Direct function call: foo()
                    func_name = child.func.id
                elif isinstance(child.func, ast.Attribute):
                    # Method call: obj.foo() - we track the method name
                    func_name = child.func.attr
                
                # Only add if it's a known internal function
                if func_name and func_name in self._all_function_names:
                    dependencies.add(func_name)
        
        return sorted(list(dependencies))
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the analysis.
        
        Returns:
            Dictionary with analysis statistics
        """
        total_functions = len(self.functions)
        async_functions = sum(1 for f in self.functions if f.is_async)
        documented_functions = sum(1 for f in self.functions if f.docstring)
        typed_functions = sum(
            1 for f in self.functions 
            if f.return_annotation or any(p.type_hint for p in f.parameters)
        )
        
        # Group by file
        files = {}
        for func in self.functions:
            if func.source_file not in files:
                files[func.source_file] = 0
            files[func.source_file] += 1
        
        return {
            "total_functions": total_functions,
            "async_functions": async_functions,
            "sync_functions": total_functions - async_functions,
            "documented_functions": documented_functions,
            "typed_functions": typed_functions,
            "documentation_rate": documented_functions / total_functions if total_functions > 0 else 0,
            "typing_rate": typed_functions / total_functions if total_functions > 0 else 0,
            "total_files": len(files),
            "total_errors": len(self.errors),
            "functions_per_file": total_functions / len(files) if files else 0,
            "top_files": sorted(files.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def get_errors(self) -> List[Dict[str, str]]:
        """Get all parsing errors encountered"""
        return self.errors
    
    def filter_by_pattern(self, pattern: str) -> List[FunctionMetadata]:
        """Filter functions by name pattern (case-insensitive)"""
        pattern_lower = pattern.lower()
        return [
            func for func in self.functions
            if pattern_lower in func.name.lower()
        ]
    
    def get_async_functions(self) -> List[FunctionMetadata]:
        """Get all async functions"""
        return [func for func in self.functions if func.is_async]
    
    def get_sync_functions(self) -> List[FunctionMetadata]:
        """Get all sync functions"""
        return [func for func in self.functions if not func.is_async]
    
    def get_function_by_name(self, name: str) -> Optional[FunctionMetadata]:
        """Get a specific function by name"""
        for func in self.functions:
            if func.name == name:
                return func
        return None
    
    def build_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Build a dependency graph of all functions.
        
        Returns:
            Dictionary mapping function names to their dependencies
        """
        graph = {}
        for func in self.functions:
            graph[func.name] = func.dependencies
        return graph
