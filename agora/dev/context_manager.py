"""
ContextManager - Lightweight Semantic Memory with sentence-transformers

Uses sentence-transformers + numpy for Python 3.13-compatible semantic search.
No C++ dependencies, no complex vector databases.

Architecture:
- Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384-dim)
- Similarity: Cosine similarity via numpy
- Ranking: Golden Score = (CosineSimilarity × 0.4) + (SuccessRate × 0.6)
- Storage: JSON + numpy arrays in .agora/memory/{session_id}/
- Migration: Auto-migrates from legacy JSON with backup
"""

import json
import os
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Semantic search dependencies (optional)
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SentenceTransformer = None
    np = None

logger = logging.getLogger(__name__)


@dataclass
class NodeMetadata:
    """
    Metadata for a saved node.
    """
    name: str
    code: str
    tags: List[str]
    created_at: str
    last_used: str
    usage_count: int
    success_count: int
    failure_count: int
    
    # Rich metadata fields
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    return_type: Optional[str] = None
    dependencies: Optional[List[str]] = None
    module_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NodeMetadata':
        return cls(**data)


class ContextManager:
    """
    Lightweight Semantic Memory with sentence-transformers + numpy.
    
    Features:
    - sentence-transformers for embeddings (Python 3.13 compatible)
    - numpy for cosine similarity (no C++ compilation)
    - Golden Score ranking (similarity + success rate)
    - Auto-migration from legacy JSON storage
    - Persistent disk storage
    
    Example:
        >>> context = ContextManager(session_id="my_project", use_semantic=True)
        >>> context.save_node("AuthNode", code, tags, docstring="Handles auth")
        >>> results = context.search_nodes("authentication", top_k=5)
        >>> # Returns nodes ranked by Golden Score
    """
    
    def __init__(
        self,
        session_id: str,
        storage_dir: str = ".agora/sessions",
        use_semantic: bool = True
    ):
        """
        Initialize ContextManager with optional semantic search.
        
        Args:
            session_id: Unique identifier for this session
            storage_dir: Base directory for session storage
            use_semantic: Use semantic embeddings (requires sentence-transformers)
        """
        self.session_id = session_id
        self.storage_dir = Path(storage_dir)
        self.session_dir = self.storage_dir / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Legacy file paths
        self.context_file = self.session_dir / "context.json"
        self.nodes_file = self.session_dir / "nodes.json"
        self.metadata_file = self.session_dir / "metadata.json"
        
        # Semantic search setup
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.model = None
        self.node_data = {}  # In-memory storage for node metadata
        self.embeddings = {}  # Node name -> embedding vector
        
        if self.use_semantic:
            self._init_semantic_search()
        else:
            if use_semantic and not SEMANTIC_AVAILABLE:
                logger.warning(
                    "Semantic search requested but dependencies not installed. "
                    "Install with: pip install -e '.[semantic]'"
                )
            # Fall back to legacy JSON storage
            self.nodes = self._load_json(self.nodes_file, {})
        
        # Load context (always JSON)
        self.context = self._load_json(self.context_file, {})
        self.metadata = self._load_json(self.metadata_file, {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_nodes": 0,
            "total_context_keys": 0,
            "semantic_enabled": self.use_semantic
        })
    
    def _init_semantic_search(self):
        """Initialize sentence-transformers model."""
        try:
            # Memory directory for persistent storage
            memory_dir = Path(".agora/memory") / self.session_id
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            metadata_path = memory_dir / "node_metadata.json"
            embeddings_path = memory_dir / "embeddings.pkl"
            
            # Load sentence transformer model
            logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)")
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            # Check if existing data exists
            if metadata_path.exists() and embeddings_path.exists():
                # Load existing data
                logger.info(f"Loading existing semantic index from {memory_dir}")
                
                with open(metadata_path, 'r') as f:
                    self.node_data = json.load(f)
                
                with open(embeddings_path, 'rb') as f:
                    self.embeddings = pickle.load(f)
                
                logger.info(f"✅ Loaded {len(self.node_data)} nodes from index")
            else:
                # New index
                logger.info("Creating new semantic index")
            
            # Auto-migrate from legacy JSON if exists
            self._auto_migrate_from_json()
            
        except Exception as e:
            logger.error(f"Failed to initialize semantic search: {e}")
            self.use_semantic = False
            self.nodes = self._load_json(self.nodes_file, {})
    
    def _auto_migrate_from_json(self):
        """
        Auto-migrate from legacy JSON storage.
        
        Creates a backup and migrates all nodes with embeddings.
        """
        if not self.nodes_file.exists():
            return
        
        logger.info("🔄 Detected legacy JSON storage. Migrating to semantic index...")
        
        # Create backup
        backup_file = self.nodes_file.with_suffix('.json.bak')
        if not backup_file.exists():
            import shutil
            shutil.copy(self.nodes_file, backup_file)
            logger.info(f"📦 Created backup: {backup_file}")
        
        # Load legacy nodes
        legacy_nodes = self._load_json(self.nodes_file, {})
        
        if not legacy_nodes:
            return
        
        migrated_count = 0
        
        for node_name, node_data in legacy_nodes.items():
            try:
                node_meta = NodeMetadata.from_dict(node_data)
                
                # Create text for embedding
                text_to_embed = f"{node_meta.name} {node_meta.docstring or ''}"
                
                # Generate embedding
                embedding = self.model.encode(text_to_embed, convert_to_numpy=True)
                
                # Store
                self.node_data[node_name] = node_meta.to_dict()
                self.embeddings[node_name] = embedding
                
                migrated_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to migrate node {node_name}: {e}")
        
        # Save migrated data
        if migrated_count > 0:
            self._save_semantic_index()
            logger.info(f"✅ Migrated {migrated_count} nodes to semantic index")
        
        # Remove old JSON file (backup exists)
        self.nodes_file.unlink()
    
    def _save_semantic_index(self):
        """Save semantic index to disk."""
        memory_dir = Path(".agora/memory") / self.session_id
        
        with open(memory_dir / "node_metadata.json", 'w') as f:
            json.dump(self.node_data, f, indent=2)
        
        with open(memory_dir / "embeddings.pkl", 'wb') as f:
            pickle.dump(self.embeddings, f)
    
    def _load_json(self, file_path: Path, default: Any) -> Any:
        """Load JSON file or return default"""
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return default
    
    def _save_json(self, file_path: Path, data: Any):
        """Save data to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_context(self, key: str, value: Any):
        """Add or update a context key-value pair."""
        self.context[key] = value
        self._save_json(self.context_file, self.context)
        
        self.metadata["total_context_keys"] = len(self.context)
        self.metadata["last_updated"] = datetime.now().isoformat()
        self._save_json(self.metadata_file, self.metadata)
    
    def get_context(self, key: str) -> Optional[Any]:
        """Get a context value by key."""
        return self.context.get(key)
    
    def get_all_context(self) -> Dict[str, Any]:
        """Get all context as a dictionary"""
        return self.context.copy()
    
    def save_node(
        self,
        node_name: str,
        node_code: str,
        tags: Optional[List[str]] = None,
        signature: Optional[str] = None,
        docstring: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        return_type: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        module_path: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Save a node with semantic embeddings.
        
        Args:
            node_name: Name of the node
            node_code: Source code of the node
            tags: List of tags for categorization
            signature: Function signature
            docstring: Full docstring
            parameters: List of parameter metadata dicts
            return_type: Return type annotation
            dependencies: List of internal function dependencies
            module_path: Python import path
            metadata: Additional metadata (deprecated)
        """
        now = datetime.now().isoformat()
        
        if self.use_semantic:
            # Semantic storage
            self._save_node_semantic(
                node_name, node_code, tags or [], signature, docstring,
                parameters, return_type, dependencies, module_path, now
            )
        else:
            # Legacy JSON storage
            self._save_node_legacy(
                node_name, node_code, tags or [], signature, docstring,
                parameters, return_type, dependencies, module_path, now
            )
        
        # Update metadata
        self.metadata["last_updated"] = now
        self._save_json(self.metadata_file, self.metadata)
    
    def _save_node_semantic(
        self, node_name, node_code, tags, signature, docstring,
        parameters, return_type, dependencies, module_path, now
    ):
        """Save node to semantic index."""
        # Check if node exists
        if node_name in self.node_data:
            # Update existing
            node_meta = NodeMetadata.from_dict(self.node_data[node_name])
            node_meta.code = node_code
            node_meta.tags = tags
            node_meta.last_used = now
            
            if signature is not None:
                node_meta.signature = signature
            if docstring is not None:
                node_meta.docstring = docstring
            if parameters is not None:
                node_meta.parameters = parameters
            if return_type is not None:
                node_meta.return_type = return_type
            if dependencies is not None:
                node_meta.dependencies = dependencies
            if module_path is not None:
                node_meta.module_path = module_path
        else:
            # New node
            node_meta = NodeMetadata(
                name=node_name,
                code=node_code,
                tags=tags,
                created_at=now,
                last_used=now,
                usage_count=0,
                success_count=0,
                failure_count=0,
                signature=signature,
                docstring=docstring,
                parameters=parameters,
                return_type=return_type,
                dependencies=dependencies,
                module_path=module_path
            )
        
        # Store metadata
        self.node_data[node_name] = node_meta.to_dict()
        
        # Create text for embedding
        text_to_embed = f"{node_name} {docstring or ''}"
        
        # Generate embedding
        embedding = self.model.encode(text_to_embed, convert_to_numpy=True)
        self.embeddings[node_name] = embedding
        
        # Save to disk
        self._save_semantic_index()
        
        # Update count
        self.metadata["total_nodes"] = len(self.node_data)
    
    def _save_node_legacy(
        self, node_name, node_code, tags, signature, docstring,
        parameters, return_type, dependencies, module_path, now
    ):
        """Save node to legacy JSON storage."""
        if node_name in self.nodes:
            node_meta = NodeMetadata.from_dict(self.nodes[node_name])
            node_meta.code = node_code
            node_meta.tags = tags
            node_meta.last_used = now
            
            if signature is not None:
                node_meta.signature = signature
            if docstring is not None:
                node_meta.docstring = docstring
            if parameters is not None:
                node_meta.parameters = parameters
            if return_type is not None:
                node_meta.return_type = return_type
            if dependencies is not None:
                node_meta.dependencies = dependencies
            if module_path is not None:
                node_meta.module_path = module_path
        else:
            node_meta = NodeMetadata(
                name=node_name,
                code=node_code,
                tags=tags,
                created_at=now,
                last_used=now,
                usage_count=0,
                success_count=0,
                failure_count=0,
                signature=signature,
                docstring=docstring,
                parameters=parameters,
                return_type=return_type,
                dependencies=dependencies,
                module_path=module_path
            )
        
        self.nodes[node_name] = node_meta.to_dict()
        self._save_json(self.nodes_file, self.nodes)
        self.metadata["total_nodes"] = len(self.nodes)
    
    def search_nodes(
        self,
        query: str,
        top_k: int = 5,
        use_grep: bool = False
    ) -> List[Tuple[NodeMetadata, float]]:
        """
        Search for nodes using semantic search or grep.
        
        Golden Score Formula:
        GoldenScore = (CosineSimilarity × 0.4) + (SuccessRate × 0.6)
        
        Args:
            query: Search query
            top_k: Number of results to return
            use_grep: Use exact string matching instead of semantic
            
        Returns:
            List of (NodeMetadata, GoldenScore) tuples, sorted by score
        """
        if use_grep:
            return self._grep_search(query, top_k)
        
        if self.use_semantic:
            return self._semantic_search(query, top_k)
        else:
            # Fall back to legacy keyword search
            return self._keyword_search(query, top_k)
    
    def _semantic_search(
        self,
        query: str,
        top_k: int
    ) -> List[Tuple[NodeMetadata, float]]:
        """
        Semantic search with Golden Score ranking.
        
        Golden Score = (CosineSimilarity × 0.4) + (SuccessRate × 0.6)
        """
        if not self.embeddings:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # Calculate cosine similarities for all nodes
        scored_results = []
        
        for node_name, node_embedding in self.embeddings.items():
            # Cosine similarity
            similarity = np.dot(query_embedding, node_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(node_embedding)
            )
            
            # Normalize to [0, 1] (cosine is in [-1, 1])
            similarity = (similarity + 1) / 2
            
            # Get node metadata
            node_dict = self.node_data[node_name]
            node_meta = NodeMetadata.from_dict(node_dict)
            
            # Calculate success rate
            success_rate = 0.5  # Default for new nodes
            if node_meta.usage_count > 0:
                success_rate = node_meta.success_count / node_meta.usage_count
            
            # Golden Score
            golden_score = (similarity * 0.4) + (success_rate * 0.6)
            
            scored_results.append((node_meta, golden_score))
        
        # Sort by Golden Score (descending)
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return scored_results[:top_k]
    
    def _keyword_search(self, query: str, top_k: int) -> List[Tuple[NodeMetadata, float]]:
        """Legacy keyword search (fallback)."""
        query_lower = query.lower()
        scored_nodes = []
        
        for node_data in self.nodes.values():
            node = NodeMetadata.from_dict(node_data)
            score = 0
            
            if query_lower in node.name.lower():
                score += 10
            for tag in node.tags:
                if query_lower in tag.lower():
                    score += 5
            if node.signature and query_lower in node.signature.lower():
                score += 4
            if node.docstring and query_lower in node.docstring.lower():
                score += 3
            
            if score > 0:
                # Normalize to [0, 1]
                normalized_score = min(score / 20.0, 1.0)
                scored_nodes.append((node, normalized_score))
        
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        return scored_nodes[:top_k]
    
    def _grep_search(self, query: str, top_k: int) -> List[Tuple[NodeMetadata, float]]:
        """Exact string matching (grep-style)."""
        results = []
        
        if self.use_semantic:
            # Search in node_data
            for node_dict in self.node_data.values():
                node = NodeMetadata.from_dict(node_dict)
                if query in node.name or (node.docstring and query in node.docstring):
                    results.append((node, 1.0))
        else:
            for node_data in self.nodes.values():
                node = NodeMetadata.from_dict(node_data)
                if query in node.name or (node.docstring and query in node.docstring):
                    results.append((node, 1.0))
        
        return results[:top_k]
    
    def record_node_outcome(self, node_name: str, success: bool):
        """
        Record the outcome of a node execution.
        Updates success_rate incrementally.
        """
        if self.use_semantic:
            if node_name in self.node_data:
                node_dict = self.node_data[node_name]
                node_dict['usage_count'] += 1
                node_dict['last_used'] = datetime.now().isoformat()
                
                if success:
                    node_dict['success_count'] += 1
                else:
                    node_dict['failure_count'] += 1
                
                # Save updated metadata
                self._save_semantic_index()
        else:
            # Legacy JSON update
            if node_name in self.nodes:
                node_meta = NodeMetadata.from_dict(self.nodes[node_name])
                node_meta.usage_count += 1
                node_meta.last_used = datetime.now().isoformat()
                
                if success:
                    node_meta.success_count += 1
                else:
                    node_meta.failure_count += 1
                
                self.nodes[node_name] = node_meta.to_dict()
                self._save_json(self.nodes_file, self.nodes)
    
    def get_node(self, node_name: str) -> Optional[NodeMetadata]:
        """Get a specific node by name."""
        if self.use_semantic:
            if node_name in self.node_data:
                return NodeMetadata.from_dict(self.node_data[node_name])
            return None
        else:
            if node_name in self.nodes:
                return NodeMetadata.from_dict(self.nodes[node_name])
            return None
    
    def get_all_nodes(self) -> List[NodeMetadata]:
        """Get all nodes as a list of NodeMetadata"""
        if self.use_semantic:
            return [NodeMetadata.from_dict(data) for data in self.node_data.values()]
        else:
            return [NodeMetadata.from_dict(data) for data in self.nodes.values()]
    
    def export_session(self) -> Dict[str, Any]:
        """
        Export entire session as JSON (snapshot format).
        
        Returns:
            Dictionary containing all session data
        """
        nodes_data = {}
        for node in self.get_all_nodes():
            nodes_data[node.name] = node.to_dict()
        
        return {
            "session_id": self.session_id,
            "metadata": self.metadata,
            "context": self.context,
            "nodes": nodes_data,
            "semantic_enabled": self.use_semantic
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the session."""
        all_nodes = self.get_all_nodes()
        total_usage = sum(n.usage_count for n in all_nodes)
        total_success = sum(n.success_count for n in all_nodes)
        
        return {
            "session_id": self.session_id,
            "total_nodes": len(all_nodes),
            "total_context_keys": len(self.context),
            "total_executions": total_usage,
            "success_rate": total_success / total_usage if total_usage > 0 else 0,
            "created_at": self.metadata.get("created_at"),
            "last_updated": self.metadata.get("last_updated"),
            "semantic_enabled": self.use_semantic
        }
