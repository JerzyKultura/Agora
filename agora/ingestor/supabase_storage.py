"""
Universal Code Ingestor - Supabase Storage Backend

Implements BaseStorage for Supabase with vector search support.
"""

import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

from agora.ingestor.storage import BaseStorage
from agora.ingestor.models import FunctionMetadata

logger = logging.getLogger(__name__)

# Lazy import
_supabase_client = None


def get_supabase_client(url: str, key: str):
    """Get or create Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        try:
            from supabase import create_client
            _supabase_client = create_client(url, key)
            logger.info("✅ Connected to Supabase")
        except ImportError:
            logger.error("supabase-py not installed. Install with: pip install supabase")
            raise
    return _supabase_client


class SupabaseStorage(BaseStorage):
    """
    Supabase storage backend for code knowledge base.
    
    Table: agora_knowledge_base
    Features:
    - Vector embeddings (384-dim)
    - Semantic search
    - Batched upserts
    - Telemetry preservation
    """
    
    TABLE_NAME = "agora_knowledge_base"
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        """
        Initialize Supabase storage.
        
        Args:
            supabase_url: Supabase project URL (or env: SUPABASE_URL)
            supabase_key: Supabase service key (or env: SUPABASE_SERVICE_KEY)
        """
        self.url = supabase_url or os.getenv('SUPABASE_URL')
        self.key = supabase_key or os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.url or not self.key:
            raise ValueError(
                "Supabase credentials required. Set SUPABASE_URL and SUPABASE_SERVICE_KEY "
                "environment variables or pass them to constructor."
            )
        
        self.client = None
    
    def connect(self) -> bool:
        """Establish connection to Supabase."""
        try:
            self.client = get_supabase_client(self.url, self.key)
            
            # Test connection
            self.client.table(self.TABLE_NAME).select("id").limit(1).execute()
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False
    
    def upsert_node(self, node: FunctionMetadata) -> bool:
        """
        Insert or update a single node.
        
        On conflict (node_hash), updates code/metadata but preserves telemetry.
        """
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            # Prepare data
            data = self._prepare_node_data(node)
            
            # Check if node exists
            existing = self.client.table(self.TABLE_NAME).select(
                "usage_count, success_rate"
            ).eq("node_hash", node.get_node_hash()).execute()
            
            # Preserve telemetry if exists
            if existing.data:
                data['usage_count'] = existing.data[0].get('usage_count', 0)
                # Calculate success_rate from success_count if available
                if 'success_rate' in existing.data[0]:
                    data['success_rate'] = existing.data[0]['success_rate']
            
            # Upsert
            result = self.client.table(self.TABLE_NAME).upsert(
                data,
                on_conflict='node_hash'
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert node {node.function_name}: {e}")
            return False
    
    def batch_upsert(self, nodes: List[FunctionMetadata]) -> int:
        """
        Insert or update multiple nodes in batches.
        
        Returns number of successfully stored nodes.
        """
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if not nodes:
            return 0
        
        success_count = 0
        batch_size = 50
        
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i + batch_size]
            
            try:
                # Prepare batch data
                batch_data = [self._prepare_node_data(node) for node in batch]
                
                # Get existing nodes to preserve telemetry
                node_hashes = [node.get_node_hash() for node in batch]
                existing = self.client.table(self.TABLE_NAME).select(
                    "node_hash, usage_count, success_rate"
                ).in_("node_hash", node_hashes).execute()
                
                # Create lookup for existing telemetry
                existing_telemetry = {
                    row['node_hash']: {
                        'usage_count': row.get('usage_count', 0),
                        'success_rate': row.get('success_rate', 0.5)
                    }
                    for row in existing.data
                }
                
                # Preserve telemetry in batch data
                for data in batch_data:
                    if data['node_hash'] in existing_telemetry:
                        telemetry = existing_telemetry[data['node_hash']]
                        data['usage_count'] = telemetry['usage_count']
                        data['success_rate'] = telemetry['success_rate']
                
                # Batch upsert
                result = self.client.table(self.TABLE_NAME).upsert(
                    batch_data,
                    on_conflict='node_hash'
                ).execute()
                
                success_count += len(batch)
                logger.info(f"Upserted batch {i//batch_size + 1}: {len(batch)} nodes")
                
            except Exception as e:
                logger.error(f"Failed to upsert batch {i//batch_size + 1}: {e}")
        
        return success_count
    
    def get_node(self, node_hash: str) -> Optional[FunctionMetadata]:
        """Retrieve a node by its hash."""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            result = self.client.table(self.TABLE_NAME).select("*").eq(
                "node_hash", node_hash
            ).execute()
            
            if result.data:
                return self._parse_node_data(result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get node {node_hash}: {e}")
            return None
    
    def search_semantic(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[tuple[FunctionMetadata, float]]:
        """
        Semantic search using vector similarity.
        
        Uses Supabase's pgvector extension for efficient similarity search.
        """
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            # Use RPC function for vector search
            result = self.client.rpc(
                'search_knowledge_base',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
            
            results = []
            for row in result.data:
                node = self._parse_node_data(row)
                similarity = row.get('similarity', 0.0)
                results.append((node, similarity))
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            # Total nodes
            total = self.client.table(self.TABLE_NAME).select(
                "id", count='exact'
            ).execute()
            
            # Languages
            languages = self.client.table(self.TABLE_NAME).select(
                "language"
            ).execute()
            
            lang_counts = {}
            for row in languages.data:
                lang = row.get('language', 'unknown')
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            
            return {
                'total_nodes': total.count,
                'languages': lang_counts,
                'table_name': self.TABLE_NAME
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def close(self):
        """Close connection (no-op for Supabase)."""
        pass
    
    def _prepare_node_data(self, node: FunctionMetadata) -> Dict[str, Any]:
        """Prepare node data for Supabase insertion."""
        now = datetime.now().isoformat()
        
        return {
            'node_hash': node.get_node_hash(),
            'function_name': node.function_name,
            'signature': node.signature,
            'source_code': node.source_code,
            'docstring': node.docstring,
            'intent_summary': node.intent_summary,
            'file_path': node.file_path,
            'line_start': node.line_start,
            'line_end': node.line_end,
            'language': node.language,
            'parameters': [
                {
                    'name': p.name,
                    'type_hint': p.type_hint,
                    'default': p.default,
                    'is_required': p.is_required
                }
                for p in node.parameters
            ],
            'return_type': node.return_type,
            'dependencies': node.dependencies,
            'embedding': node.embedding,
            'usage_count': node.usage_count,
            'success_rate': node.success_rate,
            'metadata': node.metadata,
            'updated_at': now,
            'created_at': node.created_at or now
        }
    
    def _parse_node_data(self, data: Dict[str, Any]) -> FunctionMetadata:
        """Parse Supabase row data into FunctionMetadata."""
        from agora.ingestor.models import ParameterInfo
        
        # Parse parameters
        parameters = []
        if data.get('parameters'):
            for p in data['parameters']:
                parameters.append(ParameterInfo(
                    name=p['name'],
                    type_hint=p.get('type_hint'),
                    default=p.get('default'),
                    is_required=p.get('is_required', True)
                ))
        
        return FunctionMetadata(
            function_name=data['function_name'],
            file_path=data['file_path'],
            language=data.get('language', 'python'),
            signature=data.get('signature', ''),
            source_code=data.get('source_code', ''),
            line_start=data.get('line_start', 0),
            line_end=data.get('line_end', 0),
            docstring=data.get('docstring'),
            intent_summary=data.get('intent_summary'),
            parameters=parameters,
            return_type=data.get('return_type'),
            dependencies=data.get('dependencies', []),
            embedding=data.get('embedding'),
            usage_count=data.get('usage_count', 0),
            success_rate=data.get('success_rate', 0.5),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            metadata=data.get('metadata', {})
        )
