#!/Users/anirudhanil/Desktop/agora3/Agora/.venv/bin/python3
"""
Agora Context Prime MCP Server

Provides AI-ranked debugging context to Cline/Claude via MCP tools.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx
import os
import sys
import asyncio
import json
from datetime import datetime

app = Server("agora-context")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_project_context",
            description="Get AI-ranked debugging context for the current project. Returns top failures ranked by golden score with file search hints.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project UUID (optional, uses AGORA_PROJECT_ID env var if not provided)"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["L0", "L1", "L2"],
                        "description": "Context depth: L0=minimal (3 items), L1=standard (5 items), L2=full (10 items)",
                        "default": "L1"
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    if name == "get_project_context":
        return await get_project_context(
            arguments.get("project_id"),
            arguments.get("depth", "L1")
        )
    else:
        raise ValueError(f"Unknown tool: {name}")

async def get_project_context(project_id: str = None, depth: str = "L1") -> list[TextContent]:
    """
    Fetch AI-ranked debugging context from Context Prime API.
    
    Args:
        project_id: Project UUID (uses env var if None)
        depth: L0 (minimal), L1 (standard), L2 (full)
    
    Returns:
        Formatted context with ranked failures and search hints
    """
    # Use env var if not provided
    if not project_id:
        project_id = os.getenv("AGORA_PROJECT_ID")
        if not project_id:
            return [TextContent(
                type="text",
                text="❌ Error: AGORA_PROJECT_ID not set in environment"
            )]
    
    api_key = os.getenv("AGORA_API_KEY")
    if not api_key:
        return [TextContent(
            type="text",
            text="❌ Error: AGORA_API_KEY not set in environment"
        )]
    
    backend_url = os.getenv("AGORA_BACKEND_URL", "http://localhost:8000")
    
    try:
        # Call Context Prime API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{backend_url}/v1/context/prime",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"project_id": project_id}
            )
            response.raise_for_status()
            data = response.json()
        
        # Format based on depth
        context = format_context(data, depth)
        
        # Log the context sent to Cline
        log_context_to_file(context, project_id, depth)
        
        return [TextContent(type="text", text=context)]
    
    except httpx.TimeoutException:
        return [TextContent(
            type="text",
            text=f"❌ Timeout: Backend at {backend_url} not responding (30s timeout)"
        )]
    
    except httpx.ConnectError:
        return [TextContent(
            type="text",
            text=f"❌ Connection Error: Cannot connect to {backend_url}\nIs the backend running?"
        )]
    
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 401:
            return [TextContent(type="text", text="❌ Authentication failed: Invalid API key")]
        elif status == 404:
            return [TextContent(type="text", text=f"❌ Project not found: {project_id}")]
        else:
            return [TextContent(type="text", text=f"❌ API Error {status}: {e}")]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Unexpected error: {type(e).__name__}: {str(e)}"
        )]

def log_context_to_file(context: str, project_id: str, depth: str):
    """Log the context sent to Cline for debugging/monitoring"""
    try:
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"context_{timestamp}.log")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "project_id": project_id,
            "depth": depth,
            "context": context
        }
        
        with open(log_file, "w") as f:
            json.dump(log_entry, f, indent=2)
        
        # Also append to a running log
        running_log = os.path.join(log_dir, "mcp_context.log")
        with open(running_log, "a") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Timestamp: {log_entry['timestamp']}\n")
            f.write(f"Project: {project_id}\n")
            f.write(f"Depth: {depth}\n")
            f.write(f"{'='*80}\n")
            f.write(context)
            f.write(f"\n{'='*80}\n\n")
        
        print(f"📝 Context logged to: {log_file}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Failed to log context: {e}", file=sys.stderr)

def format_context(data: dict, depth: str) -> str:
    """
    Format context in token-efficient way.
    
    L0: Minimal (3 items, ~200 tokens)
    L1: Standard (5 items, ~500 tokens) [DEFAULT]
    L2: Full (10 items, ~1500 tokens)
    
    Note: L0 and L2 are experimental. L1 is recommended for most use cases.
    """
    failures = data.get('metadata', {}).get('recent_failures', [])
    summary = data.get('context_summary', 'No summary available')
    
    # Check if no failures
    if not failures:
        return f"✅ No critical failures detected.\n\n📊 Summary: {summary}"
    
    # Determine how many items to show
    item_count = {"L0": 3, "L1": 5, "L2": 10}.get(depth, 5)
    top_failures = failures[:item_count]
    
    # Build context
    context = f"""🎯 AGORA PROJECT CONTEXT (AI-Ranked)

📊 Summary: {summary}

🔥 Top {len(top_failures)} Critical Issues (Ranked by Golden Score):

"""
    
    for i, failure in enumerate(top_failures, 1):
        attrs = failure.get('attributes', {})
        
        context += f"""#{i} {failure['name']}
   Error: {failure['error_message']}
   Time: {failure['timestamp']}
"""
        
        # Add file search hints (consistent formatting)
        if 'agora.flow' in attrs:
            workflow = attrs['agora.flow']
            workflow_file = workflow.lower().replace(' ', '_')
            context += f"   📁 Workflow: {workflow}\n"
            context += f"   � Search: {workflow_file}.py\n"
        
        if 'agora.node' in attrs:
            node = attrs['agora.node']
            node_func = node.lower().replace(' ', '_')
            context += f"   🔧 Node: {node}\n"
            context += f"   � Search: def {node_func}(\n"
        
        # Add trace/execution IDs
        context += f"   🔍 Trace ID: {failure['trace_id']}\n"
        if 'execution_id' in attrs:
            context += f"   🔍 Execution: {attrs['execution_id']}\n"
        
        context += "\n"
    
    context += """💡 RECOMMENDATION:
Focus on issue #1 first (highest golden score).
Use the file search hints above to locate the relevant code.
Check trace IDs to find related failures in telemetry.
"""
    
    return context

if __name__ == "__main__":
    # Validate environment
    if not os.getenv("AGORA_API_KEY"):
        print("❌ AGORA_API_KEY not set in environment", file=sys.stderr)
        sys.exit(1)
    
    if not os.getenv("AGORA_PROJECT_ID"):
        print("⚠️  AGORA_PROJECT_ID not set (you'll need to pass project_id to tool)", file=sys.stderr)
    
    backend_url = os.getenv("AGORA_BACKEND_URL", "http://localhost:8000")
    print("✅ Agora Context MCP Server starting...", file=sys.stderr)
    print(f"   Backend: {backend_url}", file=sys.stderr)
    
    # Run MCP server via stdio
    import mcp.server.stdio
    
    async def main():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    
    asyncio.run(main())
