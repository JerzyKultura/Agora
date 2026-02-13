# AgoraDev Guide

## What is AgoraDev?

AgoraDev is a **context management system** for AI workflows. It helps you:

- **Analyze codebases** and discover functions automatically
- **Generate Agora nodes** from existing code
- **Persist context** across AI assistant sessions
- **Search for relevant nodes** using semantic search
- **Track node usage** and success rates

## Installation

```bash
# Install with AgoraDev support
pip install -e ".[agoradev]"

# Verify installation
agora-dev --help
```

## Quick Start

### 1. Analyze a Codebase

```bash
agora-dev analyze ./my_project
```

This will:
- Scan all Python files
- Extract function metadata (signatures, docstrings, dependencies)
- Generate `@agora_node` wrapped versions
- Save to `.agora/nodes/`

### 2. Save to a Session

```bash
agora-dev analyze ./my_project --session my_session
```

This saves all discovered nodes to a persistent session for later use.

### 3. Search for Nodes

```bash
agora-dev nodes search "authentication" --session my_session
```

Find relevant nodes using keyword search.

### 4. List All Nodes

```bash
agora-dev nodes list --session my_session
```

See all nodes in a session with usage statistics.

## Core Concepts

### Sessions

Sessions are persistent storage for context and nodes:

```python
from agora.dev import ContextManager

# Create or load a session
context = ContextManager(session_id="my_project")

# Add context
context.add_context("project_type", "e-commerce")
context.add_context("user_id", "user_123")

# Save a node
context.save_node(
    node_name="AuthNode",
    node_code="...",
    tags=["auth", "security"]
)
```

**Storage location**: `.agora/sessions/{session_id}/`

### Context

Context is key-value storage that persists across sessions:

```python
# Add context
context.add_context("api_key", "sk-...")
context.add_context("environment", "production")

# Get context
api_key = context.get_context("api_key")

# Get all context
all_context = context.get_all_context()
```

### Nodes

Nodes are Agora workflow components with metadata:

```python
# Get a node
node = context.get_node("AuthNode")
print(node.name)
print(node.tags)
print(node.usage_count)
print(node.success_count)

# Search for nodes
results = context.get_relevant_nodes("authentication", max_results=5)
```

### Codebase Analysis

Analyze Python code to discover functions:

```python
from agora.dev import CodebaseAnalyzer

analyzer = CodebaseAnalyzer()
functions = analyzer.analyze_directory("./my_project")

# Get summary
summary = analyzer.get_summary()
print(f"Found {summary['total_functions']} functions")

# Filter by pattern
auth_functions = analyzer.filter_by_pattern("auth")

# Get async functions only
async_funcs = analyzer.get_async_functions()
```

### Node Generation

Auto-generate Agora nodes from functions:

```python
from agora.dev import NodeGenerator

generator = NodeGenerator()

# Generate nodes
generator.generate_node_library(
    functions=functions,
    output_dir=".agora/nodes",
    capture_io=False
)
```

## CLI Reference

### `agora-dev analyze`

Analyze a codebase and generate nodes.

```bash
agora-dev analyze <directory> [OPTIONS]

Options:
  -o, --output PATH       Output directory (default: .agora/nodes)
  -s, --session TEXT      Session ID to save nodes to
  --capture-io            Capture stdout/stderr in nodes
```

**Examples:**
```bash
# Basic analysis
agora-dev analyze ./backend

# Save to session
agora-dev analyze ./backend --session my_api

# Custom output directory
agora-dev analyze ./backend -o ./generated_nodes
```

### `agora-dev nodes`

Manage generated nodes.

#### `nodes list`

List all nodes in a session.

```bash
agora-dev nodes list --session <session_id>
```

#### `nodes search`

Search for nodes by keyword.

```bash
agora-dev nodes search <query> --session <session_id> [OPTIONS]

Options:
  -n, --max-results INT   Maximum results (default: 5)
```

**Examples:**
```bash
# Search for auth-related nodes
agora-dev nodes search "auth" --session my_api

# Get top 10 results
agora-dev nodes search "process" --session my_api -n 10
```

### `agora-dev session`

Manage sessions.

#### `session create`

Create a new session.

```bash
agora-dev session create <name>
```

#### `session list`

List all sessions.

```bash
agora-dev session list
```

#### `session summary`

Show session statistics.

```bash
agora-dev session summary <session_id>
```

#### `session export`

Export session to JSON.

```bash
agora-dev session export <session_id> [OPTIONS]

Options:
  -o, --output PATH   Output file (default: {session_id}.json)
```

#### `session import`

Import session from JSON.

```bash
agora-dev session import <file> --session <session_id>
```

## Python API

### ContextManager

```python
from agora.dev import ContextManager

context = ContextManager(session_id="my_session")

# Context management
context.add_context(key, value)
context.get_context(key)
context.get_all_context()

# Node management
context.save_node(name, code, tags, metadata)
context.get_node(name)
context.get_all_nodes()
context.get_relevant_nodes(query, max_results)

# Usage tracking
context.record_node_outcome(name, success=True)

# Maintenance
context.prune_unused_context(days=30)

# Import/Export
data = context.export_session()
context.import_session(data)

# Summary
summary = context.get_summary()
```

### CodebaseAnalyzer

```python
from agora.dev import CodebaseAnalyzer

analyzer = CodebaseAnalyzer()

# Analyze directory
functions = analyzer.analyze_directory(path, extensions=[".py"])

# Get summary
summary = analyzer.get_summary()

# Filter functions
auth_funcs = analyzer.filter_by_pattern("auth")
async_funcs = analyzer.get_async_functions()
sync_funcs = analyzer.get_sync_functions()
```

### NodeGenerator

```python
from agora.dev import NodeGenerator

generator = NodeGenerator()

# Generate single node
code = generator.wrap_function_as_node(func_metadata, capture_io=False)

# Generate library
generator.generate_node_library(
    functions=functions,
    output_dir=".agora/nodes",
    capture_io=False
)

# Get summary
summary = generator.get_summary()
```

## Use Cases

### 1. Programming: Auto-generate Workflow Nodes

```bash
# Analyze your backend code
agora-dev analyze ./backend --session backend_nodes

# Search for specific functionality
agora-dev nodes search "database" --session backend_nodes

# Use generated nodes in your workflows
```

### 2. Research: Track Papers and Concepts

```python
context = ContextManager("research_session")

# Track papers
context.add_context("paper_1", {
    "title": "Attention Is All You Need",
    "authors": ["Vaswani et al."],
    "year": 2017
})

# Save research nodes
context.save_node(
    "TransformerArchitecture",
    code="...",
    tags=["nlp", "architecture", "transformer"]
)
```

### 3. Data Analysis: Reuse Processing Pipelines

```python
# Analyze data processing scripts
analyzer = CodebaseAnalyzer()
functions = analyzer.analyze_directory("./data_pipelines")

# Generate reusable nodes
generator = NodeGenerator()
generator.generate_node_library(functions, ".agora/data_nodes")
```

## Examples

See `examples/agoradev_demo.py` for a complete example:

```bash
python examples/agoradev_demo.py
```

## Troubleshooting

### "No module named 'click'"

Install AgoraDev dependencies:
```bash
pip install -e ".[agoradev]"
```

### "Session not found"

Create the session first:
```bash
agora-dev session create my_session
```

### Generated nodes have errors

The generated nodes are **templates** - you need to:
1. Review the generated code
2. Implement the actual logic
3. Test the nodes

## Next Steps

- Read the [ContextManager API docs](../README.md#contextmanager)
- Try the [example script](../examples/agoradev_demo.py)
- Explore [advanced features](./agoradev-advanced.md)
