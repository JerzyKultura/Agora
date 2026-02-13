"""
AgoraDev Example - Analyzing a Codebase and Generating Nodes

This example demonstrates how to use AgoraDev to:
1. Analyze a Python codebase
2. Generate Agora nodes automatically
3. Save nodes to a session
4. Search for relevant nodes
"""

from agora.dev import ContextManager, CodebaseAnalyzer, NodeGenerator


def main():
    print("🚀 AgoraDev Example\n")
    
    # Step 1: Analyze the Agora codebase itself
    print("📁 Step 1: Analyzing codebase...")
    analyzer = CodebaseAnalyzer()
    functions = analyzer.analyze_directory("./agora")
    
    print(f"✅ Found {len(functions)} functions\n")
    
    # Show summary
    summary = analyzer.get_summary()
    print("📊 Analysis Summary:")
    print(f"  Total functions: {summary['total_functions']}")
    print(f"  Async functions: {summary['async_functions']}")
    print(f"  Documented: {summary['documented_functions']} ({summary['documentation_rate']:.1%})")
    print(f"  Files analyzed: {summary['total_files']}\n")
    
    # Step 2: Generate nodes
    print("🔨 Step 2: Generating nodes...")
    generator = NodeGenerator()
    generator.generate_node_library(functions[:10], ".agora/nodes")  # Generate first 10 for demo
    print()
    
    # Step 3: Save to session
    print("💾 Step 3: Saving to session...")
    session_id = "agora_demo"
    context = ContextManager(session_id)
    
    # Add some context
    context.add_context("project_type", "workflow_framework")
    context.add_context("language", "python")
    context.add_context("framework", "agora")
    
    # Save nodes to session
    for func in functions[:10]:
        node_code = generator.wrap_function_as_node(func)
        tags = generator._generate_tags(func.name)
        context.save_node(func.name, node_code, tags)
    
    print(f"✅ Saved {len(functions[:10])} nodes to session '{session_id}'\n")
    
    # Step 4: Search for nodes
    print("🔍 Step 4: Searching for nodes...")
    search_queries = ["async", "node", "flow"]
    
    for query in search_queries:
        results = context.get_relevant_nodes(query, max_results=3)
        print(f"\n  Query: '{query}' → {len(results)} results")
        for node in results:
            print(f"    • {node.name} (tags: {', '.join(node.tags)})")
    
    # Step 5: Show session summary
    print("\n\n📈 Step 5: Session Summary")
    session_summary = context.get_summary()
    print(f"  Session ID: {session_summary['session_id']}")
    print(f"  Total nodes: {session_summary['total_nodes']}")
    print(f"  Context keys: {session_summary['total_context_keys']}")
    print(f"  Created: {session_summary['created_at']}")
    
    print("\n✨ Done! Check .agora/nodes/ for generated nodes")
    print(f"   Session data saved to: .agora/sessions/{session_id}/")


if __name__ == "__main__":
    main()
