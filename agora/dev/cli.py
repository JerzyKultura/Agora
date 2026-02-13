"""
AgoraDev CLI - Command-line interface for context management

Provides commands for analyzing codebases, managing sessions,
and working with generated nodes.
"""

import click
import json
from pathlib import Path
from agora.dev.context_manager import ContextManager
from agora.dev.codebase_analyzer import CodebaseAnalyzer
from agora.dev.node_generator import NodeGenerator


@click.group()
def cli():
    """AgoraDev - Context Management for AI Workflows"""
    pass


@cli.command()
@click.argument('directory')
@click.option('--output', '-o', default='.agora/nodes', help='Output directory for generated nodes')
@click.option('--session', '-s', default=None, help='Session ID to save nodes to')
@click.option('--capture-io', is_flag=True, help='Capture stdout/stderr in nodes')
@click.option('--project-root', '-r', default=None, help='Project root for import path calculation')
def analyze(directory, output, session, capture_io, project_root):
    """
    Analyze a codebase and generate Agora nodes.
    
    Example:
        agora-dev analyze ./my_project
        agora-dev analyze ./backend --session my_session --project-root ./
    """
    click.echo(f"🔍 Analyzing codebase: {directory}")
    
    # Analyze codebase with project root
    analyzer = CodebaseAnalyzer(project_root=project_root or directory)
    try:
        functions = analyzer.analyze_directory(directory)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        return
    
    click.echo(f"✅ Found {len(functions)} functions")
    
    # Show errors if any
    errors = analyzer.get_errors()
    if errors:
        click.echo(f"⚠️  {len(errors)} files had errors (see logs)")
    
    # Show summary
    summary = analyzer.get_summary()
    click.echo(f"\n📊 Summary:")
    click.echo(f"  Total functions: {summary['total_functions']}")
    click.echo(f"  Async functions: {summary['async_functions']}")
    click.echo(f"  Documented: {summary['documented_functions']} ({summary['documentation_rate']:.1%})")
    click.echo(f"  Type-annotated: {summary['typed_functions']} ({summary['typing_rate']:.1%})")
    click.echo(f"  Files analyzed: {summary['total_files']}")
    click.echo(f"  Errors: {summary['total_errors']}")
    
    # Generate nodes
    click.echo(f"\n🔨 Generating nodes...")
    generator = NodeGenerator()
    generator.generate_node_library(functions, output, capture_io)
    
    # Save to session if specified (with rich metadata)
    if session:
        click.echo(f"\n💾 Saving to session: {session}")
        
        # Use semantic search if available
        context = ContextManager(session, use_semantic=True)
        
        if context.use_semantic:
            click.echo("✨ Semantic search enabled (using vector embeddings)")
        else:
            click.echo("⚠️  Semantic search not available. Using legacy storage.")
            click.echo("   Install with: pip install -e '.[semantic]'")
        
        for func in functions:
            node_code = generator.wrap_function_as_node(func, capture_io)
            tags = generator._generate_tags(func.name)
            
            # Save with rich metadata
            context.save_node(
                node_name=func.name,
                node_code=node_code,
                tags=tags,
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
        
        click.echo(f"✅ Saved {len(functions)} nodes with rich metadata to session")
    
    click.echo(f"\n✨ Done! Nodes saved to: {output}")


@cli.group()
def nodes():
    """Manage generated nodes"""
    pass


@nodes.command('list')
@click.option('--session', '-s', required=True, help='Session ID')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed metadata')
def list_nodes(session, verbose):
    """
    List all nodes in a session.
    
    Example:
        agora-dev nodes list --session my_session
        agora-dev nodes list --session my_session --verbose
    """
    context = ContextManager(session)
    all_nodes = context.get_all_nodes()
    
    if not all_nodes:
        click.echo("No nodes found in this session.")
        return
    
    click.echo(f"\n📦 Nodes in session '{session}':\n")
    
    for node in all_nodes:
        click.echo(f"  • {node.name}")
        
        # Show signature if available
        if node.signature:
            click.echo(f"    Signature: {node.signature}")
        
        # Show module path
        if node.module_path:
            click.echo(f"    Import: from {node.module_path} import {node.name}")
        
        click.echo(f"    Tags: {', '.join(node.tags)}")
        click.echo(f"    Usage: {node.usage_count} times")
        
        if node.usage_count > 0:
            success_rate = node.success_count / node.usage_count
            click.echo(f"    Success rate: {success_rate:.1%}")
        
        # Show verbose metadata
        if verbose:
            if node.docstring:
                click.echo(f"    Docstring: {node.docstring[:100]}...")
            
            if node.parameters:
                click.echo(f"    Parameters:")
                for param in node.parameters:
                    param_str = f"      - {param['name']}"
                    if param.get('type_hint'):
                        param_str += f": {param['type_hint']}"
                    if not param.get('required'):
                        param_str += f" = {param.get('default', 'None')}"
                    click.echo(param_str)
            
            if node.return_type:
                click.echo(f"    Returns: {node.return_type}")
            
            if node.dependencies:
                click.echo(f"    Dependencies: {', '.join(node.dependencies)}")
        
        click.echo()


@nodes.command('search')
@click.argument('query')
@click.option('--session', '-s', required=True, help='Session ID')
@click.option('--limit', '-l', default=5, help='Maximum number of results')
@click.option('--grep', is_flag=True, help='Use exact string matching instead of semantic search')
def search_nodes(query, session, limit, grep):
    """
    Search for nodes using semantic search or exact matching.
    
    Default: Semantic search with Golden Score ranking
    --grep: Exact string matching
    
    Golden Score = (CosineSimilarity × 0.4) + (SuccessRate × 0.6)
    
    Example:
        agora-dev nodes search "authentication" --session my_session
        agora-dev nodes search --grep "verify_jwt" --session my_session
    """
    context = ContextManager(session, use_semantic=True)
    
    if not context.use_semantic and not grep:
        click.echo("⚠️  Semantic search not available. Install with: pip install -e '.[semantic]'")
        click.echo("Falling back to keyword search...\n")
    
    results = context.search_nodes(query, top_k=limit, use_grep=grep)
    
    if not results:
        click.echo(f"No results found for: {query}")
        return
    
    search_type = "Exact Match" if grep else "Semantic Search (Golden Score)"
    click.echo(f"\n🔍 {search_type}: '{query}'\n")
    
    for i, (node, score) in enumerate(results, 1):
        click.echo(f"{i}. {node.name} (Score: {score:.3f})")
        
        if node.signature:
            click.echo(f"   Signature: {node.signature}")
        
        if node.module_path:
            click.echo(f"   Import: from {node.module_path} import {node.name}")
        
        if node.docstring:
            # Show first line of docstring
            first_line = node.docstring.split('\n')[0]
            click.echo(f"   Doc: {first_line[:80]}...")
        
        # Show success rate
        if node.usage_count > 0:
            success_rate = node.success_count / node.usage_count
            click.echo(f"   Success Rate: {success_rate:.1%} ({node.success_count}/{node.usage_count})")
        
        click.echo()



@cli.group()
def session():
    """Manage sessions"""
    pass


@session.command('create')
@click.argument('name')
def create_session(name):
    """
    Create a new session.
    
    Example:
        agora-dev session create my_project
    """
    context = ContextManager(name)
    click.echo(f"✅ Created session: {name}")
    click.echo(f"📁 Location: {context.session_dir}")


@session.command('list')
def list_sessions():
    """List all sessions"""
    sessions_dir = Path(".agora/sessions")
    
    if not sessions_dir.exists():
        click.echo("No sessions found.")
        return
    
    sessions = [d for d in sessions_dir.iterdir() if d.is_dir()]
    
    if not sessions:
        click.echo("No sessions found.")
        return
    
    click.echo("\n📂 Available sessions:\n")
    
    for session_dir in sessions:
        context = ContextManager(session_dir.name)
        summary = context.get_summary()
        
        click.echo(f"  • {session_dir.name}")
        click.echo(f"    Nodes: {summary['total_nodes']}")
        click.echo(f"    Context keys: {summary['total_context_keys']}")
        click.echo(f"    Last updated: {summary['last_updated']}")
        click.echo()


@session.command('export')
@click.argument('session_id')
@click.option('--output', '-o', default=None, help='Output file (default: {session_id}.json)')
def export_session(session_id, output):
    """
    Export a session to JSON.
    
    Example:
        agora-dev session export my_session
        agora-dev session export my_session -o backup.json
    """
    context = ContextManager(session_id)
    data = context.export_session()
    
    output_file = output or f"{session_id}.json"
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    click.echo(f"✅ Exported session to: {output_file}")


@session.command('import')
@click.argument('file')
@click.option('--session', '-s', required=True, help='Session ID to import into')
def import_session(file, session):
    """
    Import a session from JSON.
    
    Example:
        agora-dev session import backup.json --session my_session
    """
    with open(file, 'r') as f:
        data = json.load(f)
    
    context = ContextManager(session)
    context.import_session(data)
    
    click.echo(f"✅ Imported session from: {file}")


@session.command('summary')
@click.argument('session_id')
def session_summary(session_id):
    """
    Show session summary.
    
    Example:
        agora-dev session summary my_session
    """
    context = ContextManager(session_id)
    summary = context.get_summary()
    
    click.echo(f"\n📊 Session: {session_id}\n")
    click.echo(f"  Total nodes: {summary['total_nodes']}")
    click.echo(f"  Context keys: {summary['total_context_keys']}")
    click.echo(f"  Total executions: {summary['total_executions']}")
    click.echo(f"  Success rate: {summary['success_rate']:.1%}")
    click.echo(f"  Created: {summary['created_at']}")
    click.echo(f"  Last updated: {summary['last_updated']}")
    click.echo()


if __name__ == '__main__':
    cli()
