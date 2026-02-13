"""
NodeGenerator - Production-Ready Agora Node Generation

Generates @agora_node decorated code from discovered functions with:
- Correct Python import paths
- Preserved type hints and docstrings
- Proper async/sync handling
- Rich metadata for AI assistants
"""

from pathlib import Path
from typing import List, Optional
from agora.dev.codebase_analyzer import FunctionMetadata, ParameterMetadata
import logging

logger = logging.getLogger(__name__)


class NodeGenerator:
    """
    Generates production-ready Agora nodes from function metadata.
    
    Features:
    - Calculates correct import paths (Requirement 1)
    - Preserves full docstrings and type hints (Requirement 2)
    - Auto-tags nodes based on function names
    - Creates node library with comprehensive metadata
    
    Example:
        >>> analyzer = CodebaseAnalyzer(project_root="./my_project")
        >>> functions = analyzer.analyze_directory("./my_project/src")
        >>> generator = NodeGenerator()
        >>> generator.generate_node_library(functions, ".agora/nodes")
    """
    
    def __init__(self):
        self.generated_nodes = []
    
    def wrap_function_as_node(
        self,
        func_metadata: FunctionMetadata,
        capture_io: bool = False
    ) -> str:
        """
        Generate @agora_node wrapper code with correct imports.
        
        Requirement 1: Advanced Import Resolution
        The generated node includes the correct import statement based on
        the source file's module path.
        
        Args:
            func_metadata: Function metadata from CodebaseAnalyzer
            capture_io: Whether to capture stdout/stderr
            
        Returns:
            Generated Python code as string
        """
        # Auto-generate tags from function name
        tags = self._generate_tags(func_metadata.name)
        
        # Determine if function is async
        async_keyword = "async " if func_metadata.is_async else ""
        await_keyword = "await " if func_metadata.is_async else ""
        
        # Build the node code
        code_lines = []
        
        # Add header comment
        code_lines.append(f'"""')
        code_lines.append(f'Auto-generated Agora Node: {func_metadata.name}')
        code_lines.append(f'')
        code_lines.append(f'Source: {func_metadata.source_file}:{func_metadata.line_number}')
        code_lines.append(f'Module: {func_metadata.module_path}')
        if tags:
            code_lines.append(f'Tags: {", ".join(tags)}')
        code_lines.append(f'"""')
        code_lines.append("")
        
        # Add Agora import
        code_lines.append("from agora.agora_tracer import agora_node")
        
        # Add original function import (Requirement 1: Advanced Import Resolution)
        import_statement = f"from {func_metadata.module_path} import {func_metadata.name}"
        code_lines.append(import_statement)
        
        code_lines.append("")
        
        # Add decorator
        decorator_args = [f'name="{func_metadata.name}Node"']
        if capture_io:
            decorator_args.append("capture_io=True")
        
        code_lines.append(f"@agora_node({', '.join(decorator_args)})")
        
        # Add wrapper function definition
        code_lines.append(f"{async_keyword}def {func_metadata.name}_node(shared):")
        
        # Add docstring with metadata (Requirement 2: Rich Metadata)
        code_lines.append(f'    """')
        code_lines.append(f'    Agora node wrapper for {func_metadata.name}')
        code_lines.append(f'    ')
        
        # Include original docstring if available
        if func_metadata.docstring:
            code_lines.append(f'    Original Documentation:')
            for line in func_metadata.docstring.split('\n'):
                code_lines.append(f'    {line}')
            code_lines.append(f'    ')
        
        # Document parameters
        if func_metadata.parameters:
            code_lines.append(f'    Parameters (from shared state):')
            for param in func_metadata.parameters:
                param_doc = f'        {param.name}'
                if param.type_hint:
                    param_doc += f' ({param.type_hint})'
                if not param.is_required:
                    param_doc += f' [optional, default: {param.default_value}]'
                code_lines.append(param_doc)
            code_lines.append(f'    ')
        
        # Document return value
        if func_metadata.return_annotation:
            code_lines.append(f'    Returns: {func_metadata.return_annotation}')
            code_lines.append(f'    ')
        
        code_lines.append(f'    """')
        
        # Extract parameters from shared state
        code_lines.append("    # Extract parameters from shared state")
        for param in func_metadata.parameters:
            if param.is_required:
                code_lines.append(f'    {param.name} = shared.get("{param.name}")')
            else:
                default_val = param.default_value or "None"
                code_lines.append(f'    {param.name} = shared.get("{param.name}", {default_val})')
        
        code_lines.append("    ")
        
        # Call original function
        code_lines.append("    # Call original function")
        param_names = [p.name for p in func_metadata.parameters]
        call_args = ", ".join(param_names) if param_names else ""
        code_lines.append(f"    result = {await_keyword}{func_metadata.name}({call_args})")
        
        code_lines.append("    ")
        
        # Store result in shared state
        code_lines.append("    # Store result in shared state")
        code_lines.append(f'    shared["{func_metadata.name}_result"] = result')
        
        code_lines.append("    ")
        code_lines.append('    return "default"  # Routing key')
        
        return "\n".join(code_lines)
    
    def _generate_tags(self, function_name: str) -> List[str]:
        """Auto-generate tags from function name"""
        tags = []
        
        # Common patterns
        patterns = {
            "get": "retrieval",
            "fetch": "retrieval",
            "load": "retrieval",
            "read": "retrieval",
            "save": "storage",
            "write": "storage",
            "store": "storage",
            "update": "storage",
            "delete": "storage",
            "create": "creation",
            "generate": "creation",
            "build": "creation",
            "process": "processing",
            "transform": "processing",
            "convert": "processing",
            "validate": "validation",
            "check": "validation",
            "verify": "validation",
            "send": "communication",
            "notify": "communication",
            "email": "communication",
            "auth": "authentication",
            "login": "authentication",
            "logout": "authentication",
        }
        
        name_lower = function_name.lower()
        for pattern, tag in patterns.items():
            if pattern in name_lower:
                if tag not in tags:
                    tags.append(tag)
        
        # Add generic tag if no specific tags found
        if not tags:
            tags.append("general")
        
        return tags
    
    def generate_node_library(
        self,
        functions: List[FunctionMetadata],
        output_dir: str = ".agora/nodes",
        capture_io: bool = False
    ):
        """
        Generate a library of nodes from function metadata.
        
        Args:
            functions: List of FunctionMetadata from CodebaseAnalyzer
            output_dir: Directory to save generated nodes
            capture_io: Whether to capture stdout/stderr in nodes
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate index file
        index_lines = [
            '"""',
            'Auto-generated Agora Node Library',
            '',
            'This library contains auto-generated Agora nodes from analyzed codebase.',
            'Each node wraps an original function with proper imports and metadata.',
            '"""',
            '',
            '# Import all generated nodes',
            ''
        ]
        
        for func in functions:
            try:
                # Generate node code
                node_code = self.wrap_function_as_node(func, capture_io)
                
                # Save to individual file
                node_file = output_path / f"{func.name}_node.py"
                with open(node_file, 'w') as f:
                    f.write(node_code)
                
                # Add to index
                index_lines.append(f"from .{func.name}_node import {func.name}_node")
                
                # Track generated node with rich metadata
                self.generated_nodes.append({
                    "name": func.name,
                    "file": str(node_file),
                    "module_path": func.module_path,
                    "tags": self._generate_tags(func.name),
                    "is_async": func.is_async,
                    "source_file": func.source_file,
                    "line_number": func.line_number,
                    "signature": func.signature,
                    "docstring": func.docstring,
                    "parameters": [
                        {
                            "name": p.name,
                            "type_hint": p.type_hint,
                            "required": p.is_required,
                            "default": p.default_value
                        }
                        for p in func.parameters
                    ],
                    "return_type": func.return_annotation,
                    "dependencies": func.dependencies
                })
                
            except Exception as e:
                logger.error(f"Error generating node for {func.name}: {e}")
        
        # Save index file
        index_file = output_path / "__init__.py"
        with open(index_file, 'w') as f:
            f.write('\n'.join(index_lines))
        
        # Save comprehensive metadata (Requirement 2: Rich Metadata)
        import json
        metadata_file = output_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                "total_nodes": len(self.generated_nodes),
                "nodes": self.generated_nodes
            }, f, indent=2)
        
        logger.info(f"✅ Generated {len(self.generated_nodes)} nodes in {output_dir}")
        logger.info(f"📁 Metadata saved to {metadata_file}")
        
        print(f"✅ Generated {len(self.generated_nodes)} nodes in {output_dir}")
        print(f"📁 Metadata saved to {metadata_file}")
    
    def get_summary(self):
        """Get summary of generated nodes"""
        return {
            "total_generated": len(self.generated_nodes),
            "async_nodes": sum(1 for n in self.generated_nodes if n["is_async"]),
            "sync_nodes": sum(1 for n in self.generated_nodes if not n["is_async"]),
        }
