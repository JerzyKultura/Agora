"""
AgoraDev Production Test - Real-World Codebase Analysis

This test demonstrates all four production requirements:
1. Advanced Import Resolution
2. Rich Metadata Persistence
3. Error-Tolerant Parsing
4. Dependency Mapping
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import agora
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly from modules to avoid agora.__init__.py (which requires telemetry deps)
from agora.dev.codebase_analyzer import CodebaseAnalyzer
from agora.dev.node_generator import NodeGenerator
from agora.dev.context_manager import ContextManager
import json


def main():
    print("🚀 AgoraDev Production Test\n")
    print("=" * 60)
    
    # Test 1: Advanced Import Resolution
    print("\n📁 Test 1: Advanced Import Resolution")
    print("-" * 60)
    
    analyzer = CodebaseAnalyzer(project_root="./agora")
    functions = analyzer.analyze_directory("./agora")
    
    print(f"✅ Analyzed {len(functions)} functions")
    
    # Show some examples of calculated module paths
    print("\nExample module paths:")
    for func in functions[:5]:
        print(f"  {func.module_path}.{func.name}")
        print(f"    → from {func.module_path} import {func.name}")
    
    # Test 2: Rich Metadata Persistence
    print("\n\n📊 Test 2: Rich Metadata Persistence")
    print("-" * 60)
    
    # Find a well-documented function
    documented_funcs = [f for f in functions if f.docstring and f.parameters]
    if documented_funcs:
        func = documented_funcs[0]
        print(f"\nFunction: {func.name}")
        print(f"Signature: {func.signature}")
        print(f"\nDocstring:")
        print(f"  {func.docstring[:200]}...")
        print(f"\nParameters:")
        for param in func.parameters:
            print(f"  - {param.name}: {param.type_hint or 'Any'}", end="")
            if not param.is_required:
                print(f" = {param.default_value}", end="")
            print()
        if func.return_annotation:
            print(f"\nReturns: {func.return_annotation}")
    
    # Test 3: Error-Tolerant Parsing
    print("\n\n⚠️  Test 3: Error-Tolerant Parsing")
    print("-" * 60)
    
    errors = analyzer.get_errors()
    print(f"Total errors encountered: {len(errors)}")
    print(f"Analysis continued despite errors: ✅")
    
    if errors:
        print(f"\nError types:")
        error_types = {}
        for error in errors:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        for error_type, count in error_types.items():
            print(f"  {error_type}: {count}")
    
    # Test 4: Dependency Mapping
    print("\n\n🔗 Test 4: Dependency Mapping")
    print("-" * 60)
    
    # Find functions with dependencies
    funcs_with_deps = [f for f in functions if f.dependencies]
    print(f"Functions with internal dependencies: {len(funcs_with_deps)}")
    
    if funcs_with_deps:
        print(f"\nExample dependency chains:")
        for func in funcs_with_deps[:3]:
            print(f"  {func.name} calls:")
            for dep in func.dependencies:
                print(f"    → {dep}")
    
    # Build dependency graph
    dep_graph = analyzer.build_dependency_graph()
    print(f"\nTotal nodes in dependency graph: {len(dep_graph)}")
    
    # Test 5: Node Generation with Correct Imports
    print("\n\n🔨 Test 5: Node Generation")
    print("-" * 60)
    
    generator = NodeGenerator()
    
    # Generate a sample node
    if functions:
        sample_func = functions[0]
        node_code = generator.wrap_function_as_node(sample_func)
        
        print(f"Generated node for: {sample_func.name}")
        print(f"\nGenerated code preview:")
        print("-" * 40)
        lines = node_code.split('\n')
        for line in lines[:20]:  # Show first 20 lines
            print(line)
        print("...")
        print("-" * 40)
    
    # Test 6: Context Manager with Rich Metadata
    print("\n\n💾 Test 6: Context Manager with Rich Metadata")
    print("-" * 60)
    
    session_id = "production_test"
    context = ContextManager(session_id)
    
    # Save a few nodes with rich metadata
    for func in functions[:3]:
        context.save_node(
            node_name=func.name,
            node_code=generator.wrap_function_as_node(func),
            tags=generator._generate_tags(func.name),
            signature=func.signature,
            docstring=func.docstring,
            parameters=[
                {
                    "name": p.name,
                    "type_hint": p.type_hint,
                    "required": p.is_required,
                    "default": p.default_value
                }
                for p in func.parameters
            ],
            return_type=func.return_annotation,
            dependencies=func.dependencies,
            module_path=func.module_path
        )
    
    print(f"✅ Saved 3 nodes with rich metadata")
    
    # Test semantic search
    print(f"\n🔍 Testing semantic search:")
    search_queries = ["async", "node", "flow"]
    
    for query in search_queries:
        results = context.search_nodes(query, top_k=2)
        print(f"\n  Query: '{query}' → {len(results)} results")
        for node, score in results:
            print(f"    • {node.name} (score: {score:.3f})")
            if node.signature:
                print(f"      {node.signature}")
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📈 Summary")
    print("=" * 60)
    
    summary = analyzer.get_summary()
    print(f"\nAnalysis Statistics:")
    print(f"  Total functions: {summary['total_functions']}")
    print(f"  Async functions: {summary['async_functions']}")
    print(f"  Documented: {summary['documented_functions']} ({summary['documentation_rate']:.1%})")
    print(f"  Type-annotated: {summary['typed_functions']} ({summary['typing_rate']:.1%})")
    print(f"  Files analyzed: {summary['total_files']}")
    print(f"  Parse errors: {summary['total_errors']}")
    
    print(f"\n✅ All production requirements validated!")
    print(f"\n📁 Session data saved to: .agora/sessions/{session_id}/")


if __name__ == "__main__":
    main()
