"""
Direct Supabase telemetry uploader - No backend API needed!

This uploads telemetry data directly to Supabase from your Python scripts.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
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
        project_id: Optional[str] = None
    ):
        self.project_name = project_name or "default"
        self.supabase_url = supabase_url or os.environ.get("VITE_SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("VITE_SUPABASE_ANON_KEY")
        self.api_key = api_key or os.environ.get("AGORA_API_KEY")
        self.force_project_id = project_id or os.environ.get("AGORA_PROJECT_ID")

        self.execution_id: Optional[str] = None
        self.workflow_id: Optional[str] = None
        self.project_id: Optional[str] = None
        self.organization_id: Optional[str] = None

        self.enabled = bool(self.supabase_url and self.supabase_key and SUPABASE_AVAILABLE)

        if self.enabled:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            print(f"✅ Supabase uploader enabled for project: {self.project_name}")
            if self.force_project_id:
                print(f"DEBUG: Using forced Project ID: {self.force_project_id}")
        else:
            self.client = None
            print(f"DEBUG: SupabaseUploader NOT enabled. URL={bool(self.supabase_url)}, Key={bool(self.supabase_key)}, Lib={SUPABASE_AVAILABLE}")
            if not SUPABASE_AVAILABLE:
                print("⚠️  supabase-py not installed - run: pip install supabase")
            if not self.supabase_url or not self.supabase_key:
                print("⚠️  VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not set")

    def _get_or_create_org(self) -> Optional[str]:
        """Get the first available organization"""
        if not self.enabled:
            return None

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

    def _get_or_create_project(self) -> Optional[str]:
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

    def _get_or_create_workflow(self, workflow_name: str) -> Optional[str]:
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

    def _register_node(self, node_name: str, node_type: str = "async_node", description: str = "") -> Optional[str]:
        """Register a node in the database for the workflow graph.
        
        Returns the node ID if successful, None otherwise.
        """
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
                return result.data[0]["id"]
            
            # Create new node with metadata
            result = self.client.table("nodes").insert({
                "workflow_id": self.workflow_id,
                "name": node_name,
                "type": node_type,
                "config": {
                    "description": description,
                    "node_type": node_type
                }
            }).execute()
            
            return result.data[0]["id"]
        except Exception as e:
            print(f"⚠️  Failed to register node {node_name}: {e}")
            return None

    def _register_edge(self, source_node_name: str, target_node_name: str, label: str = "") -> Optional[str]:
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
            
            # Create new edge
            result = self.client.table("edges").insert({
                "workflow_id": self.workflow_id,
                "from_node_id": source_id,
                "to_node_id": target_id,
                "action": label or "default"
            }).execute()
            
            return result.data[0]["id"]
        except Exception as e:
            print(f"⚠️  Failed to register edge {source_node_name} -> {target_node_name}: {e}")
            return None

    def register_workflow_graph(self, flow_graph: Dict[str, Any]):
        """Register the complete workflow graph (nodes and edges) from a flow.to_dict() output.
        
        Args:
            flow_graph: Output from AsyncFlow.to_dict() with 'nodes' and 'edges' keys
        """
        if not self.enabled or not self.workflow_id:
            return
        
        nodes = flow_graph.get("nodes", [])
        edges = flow_graph.get("edges", [])
        
        # Register all nodes first
        for node in nodes:
            node_name = node.get("name", node) if isinstance(node, dict) else node
            self._register_node(node_name, node_type="async_node")
        
        # Then register all edges
        for edge in edges:
            source = edge.get("from", "")
            target = edge.get("to", "")
            action = edge.get("action", "")
            if source and target:
                self._register_edge(source, target, action)

    async def start_execution(
        self,
        workflow_name: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Start a new execution"""
        if not self.enabled:
            return None

        try:
            # Setup org, project, workflow
            # Setup org, project, workflow
            if not self.project_id:
                # If we have a forced project ID, use it and skip org check
                if self.force_project_id:
                    self.project_id = self.force_project_id
                else:
                    if not self.organization_id:
                        self.organization_id = self._get_or_create_org()
                    self.project_id = self._get_or_create_project()
            if not self.workflow_id:
                print(f"DEBUG: Getting/Creating Workflow: {workflow_name}")
                self.workflow_id = self._get_or_create_workflow(workflow_name)

            if not self.workflow_id:
                print("⚠️  Failed to setup workflow - checking permissions...")
                return None

            print(f"DEBUG: Creating Execution for Workflow: {self.workflow_id}")
            # Create execution
            result = self.client.table("executions").insert({
                "workflow_id": self.workflow_id,
                "status": "running",
                "input_data": input_data or {},
                "started_at": datetime.utcnow().isoformat()
            }).execute()

            self.execution_id = result.data[0]["id"]
            print(f"✅ Started execution: {self.execution_id}")
            return self.execution_id

        except Exception as e:
            print(f"⚠️  Failed to start execution: {e}")
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

            started_at = datetime.fromisoformat(exec_result.data["started_at"].replace("Z", "+00:00"))
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at.replace(tzinfo=None)).total_seconds() * 1000)

            # Update execution
            self.client.table("executions").update({
                "status": status,
                "completed_at": completed_at.isoformat(),
                "duration_ms": duration_ms,
                "output_data": output_data,
                "error_message": error_message
            }).eq("id", self.execution_id).execute()

            print(f"✅ Completed execution: {self.execution_id} ({status})")

        except Exception as e:
            print(f"⚠️  Failed to complete execution: {e}")

    async def add_spans(self, spans: List[Dict[str, Any]]):
        """Add raw telemetry spans"""
        if not self.enabled or not self.execution_id:
            return

        try:
            formatted_spans = []
            for span in spans:
                formatted_spans.append({
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
                    "events": span.get("events", [])
                })

            if formatted_spans:
                self.client.table("telemetry_spans").insert(formatted_spans).execute()
        except Exception as e:
            print(f"⚠️  Failed to add spans: {e}")

    def add_node_execution(
        self,
        node_name: str,
        node_type: str,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        prep_duration_ms: Optional[int] = None,
        exec_duration_ms: Optional[int] = None,
        post_duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0
    ):
        """Add node execution data"""
        if not self.enabled or not self.execution_id or not self.workflow_id:
            return

        try:
            # Get or create node
            node_result = self.client.table("nodes")\
                .select("id")\
                .eq("workflow_id", self.workflow_id)\
                .eq("name", node_name)\
                .limit(1)\
                .execute()

            if node_result.data:
                node_id = node_result.data[0]["id"]
            else:
                # Create node
                new_node = self.client.table("nodes").insert({
                    "workflow_id": self.workflow_id,
                    "name": node_name,
                    "type": node_type,
                    "config": {}
                }).execute()
                node_id = new_node.data[0]["id"]

            # Insert node execution
            self.client.table("node_executions").insert({
                "execution_id": self.execution_id,
                "node_id": node_id,
                "status": status,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat() if completed_at else None,
                "prep_duration_ms": prep_duration_ms,
                "exec_duration_ms": exec_duration_ms,
                "post_duration_ms": post_duration_ms,
                "error_message": error_message,
                "retry_count": retry_count
            }).execute()

        except Exception as e:
            print(f"⚠️  Failed to add node execution: {e}")


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
