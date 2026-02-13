"""
Universal Code Ingestor - Base Storage Interface

Abstract base class for storage backends (Supabase, SQLite, JSON, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from agora.ingestor.models import FunctionMetadata


class BaseStorage(ABC):
    """
    Abstract base class for code knowledge storage.
    
    Implementations:
    - SupabaseStorage: Cloud vector database
    - LocalStorage: SQLite + JSON (future)
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to storage backend.
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def upsert_node(self, node: FunctionMetadata) -> bool:
        """
        Insert or update a single node.
        
        Args:
            node: Function metadata to store
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def batch_upsert(self, nodes: List[FunctionMetadata]) -> int:
        """
        Insert or update multiple nodes in a batch.
        
        Args:
            nodes: List of function metadata to store
            
        Returns:
            Number of nodes successfully stored
        """
        pass
    
    @abstractmethod
    def get_node(self, node_hash: str) -> Optional[FunctionMetadata]:
        """
        Retrieve a node by its hash.
        
        Args:
            node_hash: Unique hash of the node
            
        Returns:
            FunctionMetadata if found, None otherwise
        """
        pass
    
    @abstractmethod
    def search_semantic(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[tuple[FunctionMetadata, float]]:
        """
        Semantic search using vector similarity.
        
        Args:
            query_embedding: Query vector
            limit: Maximum results
            threshold: Minimum similarity score
            
        Returns:
            List of (node, similarity_score) tuples
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with stats (total_nodes, languages, etc.)
        """
        pass
    
    @abstractmethod
    def close(self):
        """Close connection to storage backend."""
        pass
