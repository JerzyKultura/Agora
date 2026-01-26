"""
Direct Supabase telemetry uploader - No backend API needed!

This uploads telemetry data directly to Supabase from your Python scripts.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None
    Client = None


class SupabaseUploader:
    """Upload telemetry directly to Supabase database"""

    def __init__(
        self,
        project_name: Optional[str] = None,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        org_id: Optional[str] = None
    ):
        self.project_name = project_name or "default"
        self.supabase_url = supabase_url or os.environ.get("VITE_SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("VITE_SUPABASE_ANON_KEY")
        self.api_key = api_key or os.environ.get("AGORA_API_KEY")
        self.force_project_id = project_id or os.environ.get("AGORA_PROJECT_ID")
        self.force_org_id = org_id or os.environ.get("AGORA_ORG_ID")

        self.execution_id: Optional[str] = None
        self.workflow_id: Optional[str] = None
        self.project_id: Optional[str] = None
        self.organization_id: Optional[str] = None
        
        # Batching
        self.span_buffer: List[Dict[str, Any]] = []
        self.batch_size = 10

        self.enabled = bool(self.supabase_url and self.supabase_key and SUPABASE_AVAILABLE)

        if self.enabled:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            print(f"✅ Supabase uploader enabled for project: {self.project_name}")
            if self.api_key:
                masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
                print(f"🔑 Agora API Key verified: {masked_key}")
        else:
            self.client = None
            if not SUPABASE_AVAILABLE:
                print("⚠️  supabase-py not installed - run: pip install supabase")
            if not self.supabase_url or not self.supabase_key:
                print("⚠️  VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not set")

    async def _with_retry(self, func, *args, max_retries=3, initial_delay=1, data_to_retry=None, **kwargs):
        """Execute a function with exponential backoff retry.
        If data_to_retry is provided, it will attempt to strip missing columns on PGRST204.
        """
        delay = initial_delay
        current_data = data_to_retry
        
        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                # Check for "Missing Column" error (PGRST204)
                if "PGRST204" in error_str and current_data is not None:
                    import re
                    match = re.search(r"Could not find the '(.+?)' column", error_str)
                    if match:
                        missing_col = match.group(1)
                        print(f"⚠️  Schema Mismatch: Column '{missing_col}' not found. Stripping and retrying...")
                        
                        # Strip the missing column from data
                        if isinstance(current_data, list):
                            for item in current_data:
                                if missing_col in item:
                                    del item[missing_col]
                        elif isinstance(current_data, dict):
                            if missing_col in current_data:
                                del current_data[missing_col]
                        
                        # We need to recreate the request builder if we stripped columns
                        # This is tricky because func is already bound.
                        # For now, we rely on the caller to use this smartly or we handle it in specific methods.
                
                if attempt < max_retries - 1:
                    # Don't print full error for PGRST204 if we're trying to fix it
                    if "PGRST204" not in error_str:
                        print(f"⚠️  Upload attempt {attempt+1} failed ({e}), retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    if "PGRST204" in error_str:
                        print(f"❌  Upload failed: Your database schema is out of sync. Please run the migrations in all_migrations.sql.")
                    else:
                        print(f"❌  Upload failed after {max_retries} attempts: {e}")
        
        return None

    async def _execute_resilient(self, table_name, data, method="insert", query_params=None):
        """Execute a Supabase request (insert/update) with resilience against missing columns."""
        if not self.enabled:
            return None

        current_data = data
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if method == "insert":
                    builder = self.client.table(table_name).insert(current_data)
                elif method == "update":
                    builder = self.client.table(table_name).update(current_data)
                
                if query_params:
                    for key, val in query_params.items():
                        builder = builder.eq(key, val)
                
                return builder.execute()
            except Exception as e:
                error_str = str(e)
                if "PGRST204" in error_str:
                    import re
                    match = re.search(r"Could not find the '(.+?)' column", error_str)
                    if match:
                        missing_col = match.group(1)
                        # Strip the missing column from data
                        if isinstance(current_data, list):
                            for item in current_data:
                                if missing_col in item:
                                    del item[missing_col]
                        elif isinstance(current_data, dict):
                            if missing_col in current_data:
                                del current_data[missing_col]
                        
                        # Continue to next retry with stripped data
                        continue
                
                # If not PGRST204 or no more retries for other reasons
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise e
        return None

    async def _get_or_create_org(self) -> Optional[str]:
        """Get the first available organization"""
        if not self.enabled:
            return None
        
        # If org ID is forced via environment variable, use it
        if self.force_org_id:
            return self.force_org_id

        try:
            # Get first org (in production, you'd auth and get user's org)
            result = self.client.table("organizations").select("id").limit(1).execute()
            if result.data:
                return result.data[0]["id"]

            # Create default org if none exists
            result = self.client.table("organizations").insert({
                "name": "Default Organization"
            }).execute()
            return result.data[0]["id"]
        except Exception as e:
            print(f"⚠️  Failed to get organization: {e}")
            return None

    async def _get_or_create_project(self) -> Optional[str]:
        """Get or create project"""
        if not self.enabled:
            return None
            
        if self.force_project_id:
            # Assume it exists or at least we should use it
            return self.force_project_id

        if not self.organization_id:
            return None

        try:
            # Try to find existing project
            result = self.client.table("projects")\
                .select("id")\
                .eq("organization_id", self.organization_id)\
                .eq("name", self.project_name)\
                .limit(1)\
                .execute()

            if result.data:
                return result.data[0]["id"]

            # Create new project
            result = self.client.table("projects").insert({
                "organization_id": self.organization_id,
                "name": self.project_name,
                "description": "Auto-created from telemetry"
            }).execute()
            return result.data[0]["id"]
        except Exception as e:
            print(f"⚠️  Failed to get/create project: {e}")
            return None

    async def _get_or_create_workflow(self, workflow_name: str) -> Optional[str]:
        """Get or create workflow"""
        if not self.enabled or not self.project_id:
            return None

        try:
            # Try to find existing workflow
            result = self.client.table("workflows")\
                .select("id")\
                .eq("project_id", self.project_id)\
                .eq("name", workflow_name)\
                .limit(1)\
                .execute()

            if result.data:
                return result.data[0]["id"]

            # Create new workflow
            result = self.client.table("workflows").insert({
                "project_id": self.project_id,
                "name": workflow_name,
                "type": "sequential",
                "config": {}
            }).execute()
            return result.data[0]["id"]
        except Exception as e:
            print(f"⚠️  Failed to get/create workflow: {e}")
            return None

    async def _register_node(self, node_name: str, node_type: str = "async_node", description: str = "", code: Optional[str] = None) -> Optional[str]:
        """Register a node in the database for the workflow graph."""
        if not self.enabled or not self.workflow_id:
            return None
        
        try:
            # Check if node already exists
            result = self.client.table("nodes")\
                .select("id")\
                .eq("workflow_id", self.workflow_id)\
                .eq("name", node_name)\
                .limit(1)\
                .execute()
            
            if result.data:
                node_id = result.data[0]["id"]
                # Update code if provided (to refresh metadata from previous empty runs)
                if code:
                    self.client.table("nodes").update({"code": code}).eq("id", node_id).execute()
                return node_id
            
            # Create new node with metadata resiliently
            result = await self._execute_resilient("nodes", {
                "workflow_id": self.workflow_id,
                "name": node_name,
                "type": node_type,
                "code": code,
                "config": {
                    "description": description,
                    "node_type": node_type
                }
            }, method="insert")
            return result.data[0]["id"] if result and result.data else None
        except Exception:
            return None

    async def _register_edge(self, source_node_name: str, target_node_name: str, label: str = "") -> Optional[str]:
        """Register an edge (connection) between two nodes.
        
        Returns the edge ID if successful, None otherwise.
        """
        if not self.enabled or not self.workflow_id:
            return None
        
        try:
            # Get source node ID
            source_result = self.client.table("nodes")\
                .select("id")\
                .eq("workflow_id", self.workflow_id)\
                .eq("name", source_node_name)\
                .limit(1)\
                .execute()
            
            if not source_result.data:
                return None
            source_id = source_result.data[0]["id"]
            
            # Get target node ID
            target_result = self.client.table("nodes")\
                .select("id")\
                .eq("workflow_id", self.workflow_id)\
                .eq("name", target_node_name)\
                .limit(1)\
                .execute()
            
            if not target_result.data:
                return None
            target_id = target_result.data[0]["id"]
            
            # Check if edge already exists
            edge_result = self.client.table("edges")\
                .select("id")\
                .eq("workflow_id", self.workflow_id)\
                .eq("from_node_id", source_id)\
                .eq("to_node_id", target_id)\
                .limit(1)\
                .execute()
            
            if edge_result.data:
                return edge_result.data[0]["id"]
            
            # Create new edge resiliently
            result = await self._execute_resilient("edges", {
                "workflow_id": self.workflow_id,
                "from_node_id": source_id,
                "to_node_id": target_id,
                "action": label or "default"
            }, method="insert")
            
            return result.data[0]["id"] if result and result.data else None
        except Exception:
            return None

    async def register_workflow_graph(self, flow_graph: Dict[str, Any]):
        """Register the complete workflow graph (nodes and edges) from a flow.to_dict() output."""
        if not self.enabled or not self.workflow_id:
            return
        
        nodes = flow_graph.get("nodes", [])
        edges = flow_graph.get("edges", [])
        
        # Register all nodes first
        for node in nodes:
            node_name = node.get("name", node) if isinstance(node, dict) else node
            node_code = node.get("code") if isinstance(node, dict) else None
            await self._register_node(node_name, code=node_code)
        
        # Register all edges
        for edge in edges:
            # Handle both possible naming conventions
            source = edge.get("from") or edge.get("source")
            target = edge.get("to") or edge.get("target")
            label = edge.get("action") or edge.get("label", "")
            
            if source and target:
                await self._register_edge(source, target, label)

    async def _create_standalone_execution(self) -> Optional[str]:
        """Create a standalone execution for LLM calls without a workflow"""
        if not self.enabled:
            return None

        try:
            # 1. Org/Project setup
            if not self.project_id:
                if self.force_project_id:
                    self.project_id = self.force_project_id
                else:
                    if not self.organization_id:
                        self.organization_id = await self._get_or_create_org()
                    self.project_id = await self._get_or_create_project()

            # 2. Get or create a "Standalone LLM Calls" workflow
            if not self.workflow_id:
                self.workflow_id = await self._get_or_create_workflow("Standalone LLM Calls")

            if not self.workflow_id:
                return None

            # 3. Create execution
            result = await self._execute_resilient("executions", {
                "workflow_id": self.workflow_id,
                "status": "running",
                "input_data": {"type": "standalone_llm_calls"},
                "started_at": datetime.now(timezone.utc).isoformat()
            }, method="insert")

            if result and result.data:
                self.execution_id = result.data[0]["id"]
                print(f"📊 Created standalone execution: {self.execution_id}")
                return self.execution_id
            return None

        except Exception as e:
            print(f"⚠️  Failed to create standalone execution: {e}")
            return None

    async def start_execution(self, workflow_name: str, input_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Start a new workflow execution"""
        if not self.enabled:
            return None

        try:
            # 1. Org/Project/Workflow setup
            if not self.project_id:
                if self.force_project_id:
                    self.project_id = self.force_project_id
                else:
                    if not self.organization_id:
                        self.organization_id = await self._get_or_create_org()
                    self.project_id = await self._get_or_create_project()

            if not self.workflow_id:
                self.workflow_id = await self._get_or_create_workflow(workflow_name)

            if not self.workflow_id:
                return None

            # 2. Create execution resiliently
            result = await self._execute_resilient("executions", {
                "workflow_id": self.workflow_id,
                "status": "running",
                "input_data": input_data or {},
                "started_at": datetime.now(timezone.utc).isoformat()
            }, method="insert")

            if result and result.data:
                self.execution_id = result.data[0]["id"]
                return self.execution_id
            return None

        except Exception:
            return None

    async def complete_execution(
        self,
        status: str = "success",
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """Complete the execution"""
        if not self.enabled or not self.execution_id:
            return

        try:
            # Get execution to calculate duration
            exec_result = self.client.table("executions")\
                .select("started_at")\
                .eq("id", self.execution_id)\
                .single()\
                .execute()

            # Parse started_at and ensure it's timezone-aware
            started_at_str = exec_result.data["started_at"]
            if started_at_str.endswith('Z'):
                started_at_str = started_at_str[:-1] + '+00:00'
            started_at = datetime.fromisoformat(started_at_str)
            
            # Ensure started_at is timezone-aware
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            
            completed_at = datetime.now(timezone.utc)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            # Update execution
            await self._execute_resilient("executions", {
                "status": status,
                "completed_at": completed_at.isoformat(),
                "duration_ms": duration_ms,
                "output_data": output_data,
                "error_message": error_message
            }, method="update", query_params={"id": self.execution_id})

            await self.flush_spans() # Flush any remaining spans
            print(f"✅ Completed execution: {self.execution_id} ({status})")

        except Exception as e:
            print(f"⚠️  Failed to complete execution: {e}")

    async def flush_spans(self):
        """Flush buffered spans to Supabase"""
        if not self.enabled or not self.span_buffer or not self.execution_id:
            return

        try:
            spans_to_upload = self.span_buffer.copy()
            self.span_buffer = []
            await self._execute_resilient("telemetry_spans", spans_to_upload, method="insert")
        except Exception as e:
            print(f"⚠️  Failed to flush spans: {e}")

    async def add_spans(self, spans: List[Dict[str, Any]]):
        """Add spans to the buffer"""
        if not self.enabled:
            return

        # Auto-create execution if none exists (for standalone LLM calls)
        if not self.execution_id:
            await self._create_standalone_execution()
            if not self.execution_id:
                return  # Still no execution_id, bail out

        try:
            # Get organization ID for multi-tenant filtering
            if not self.organization_id:
                self.organization_id = await self._get_or_create_org()
            
            org_id = self.organization_id
            
            for span in spans:
                self.span_buffer.append({
                    "execution_id": self.execution_id,
                    "span_id": span.get("span_id"),
                    "trace_id": span.get("trace_id"),
                    "parent_span_id": span.get("parent_span_id"),
                    "name": span.get("name"),
                    "kind": span.get("kind"),
                    "status": span.get("status"),
                    "start_time": span.get("start_time"),
                    "end_time": span.get("end_time"),
                    "duration_ms": span.get("duration_ms"),
                    "attributes": span.get("attributes", {}),
                    "events": span.get("events", []),
                    "tokens_used": span.get("tokens_used"),
                    "estimated_cost": span.get("estimated_cost"),
                    "organization_id": org_id  # Required by database schema
                })

            if len(self.span_buffer) >= self.batch_size:
                await self.flush_spans()
        except Exception as e:
            print(f"⚠️  Failed to add spans to buffer: {e}")

    async def add_node_execution(
        self,
        node_name: str,
        node_type: str,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        prep_duration_ms: Optional[int] = None,
        exec_duration_ms: Optional[int] = None,
        code: Optional[str] = None,
        post_duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0,
        tokens_used: Optional[int] = None,
        estimated_cost: Optional[float] = None
    ):
        """Add node execution data"""
        if not self.enabled or not self.execution_id or not self.workflow_id:
            return

        try:
            # 1. Register node if needed
            node_id = await self._register_node(node_name, node_type, code=code)
            if not node_id:
                return

            # Insert node execution resiliently
            await self._execute_resilient("node_executions", {
                "execution_id": self.execution_id,
                "node_id": node_id,
                "status": status,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat() if completed_at else None,
                "prep_duration_ms": prep_duration_ms,
                "exec_duration_ms": exec_duration_ms,
                "post_duration_ms": post_duration_ms,
                "error_message": error_message,
                "retry_count": retry_count,
                "tokens_used": tokens_used,
                "estimated_cost": estimated_cost
            }, method="insert")

        except Exception as e:
            print(f"⚠️  Failed to add node execution telemetry for '{node_name}': {e}")


def create_supabase_uploader(
    project_name: str,
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None
) -> SupabaseUploader:
    """
    Create a Supabase uploader for direct database telemetry

    Usage:
        uploader = create_supabase_uploader("my_project")
        await uploader.start_execution("my_workflow")
        uploader.add_node_execution("node1", "async_node", "success", datetime.now())
        await uploader.complete_execution()
    """
    return SupabaseUploader(
        project_name=project_name,
        supabase_url=supabase_url,
        supabase_key=supabase_key
    )
