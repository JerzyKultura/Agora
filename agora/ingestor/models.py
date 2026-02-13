"""
Universal Code Ingestor - Data Models

Defines the core data structures for code extraction and storage.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class ParameterInfo:
    """Information about a function parameter."""
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None
    is_required: bool = True


@dataclass
class FunctionMetadata:
    """
    Complete metadata for a function extracted from source code.
    """
    # Core identification
    function_name: str
    file_path: str  # Relative path from project root
    language: str = "python"
    
    # Source code
    signature: str = ""
    source_code: str = ""
    line_start: int = 0
    line_end: int = 0
    
    # Documentation
    docstring: Optional[str] = None
    intent_summary: Optional[str] = None  # Generated if no docstring
    
    # Type information
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)  # Internal function calls
    
    # Semantic
    embedding: Optional[List[float]] = None
    
    # Telemetry (preserved on updates)
    usage_count: int = 0
    success_rate: float = 0.5
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        # Convert ParameterInfo objects to dicts
        data['parameters'] = [
            {
                'name': p.name,
                'type_hint': p.type_hint,
                'default': p.default,
                'is_required': p.is_required
            }
            for p in self.parameters
        ]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FunctionMetadata':
        """Create from dictionary."""
        # Convert parameter dicts to ParameterInfo objects
        if 'parameters' in data and data['parameters']:
            data['parameters'] = [
                ParameterInfo(**p) if isinstance(p, dict) else p
                for p in data['parameters']
            ]
        return cls(**data)
    
    def get_node_hash(self) -> str:
        """
        Generate unique hash for this function.
        
        Hash = sha256(file_path + function_name + language)
        """
        import hashlib
        hash_input = f"{self.file_path}::{self.function_name}::{self.language}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def get_embedding_text(self) -> str:
        """Get text to use for embedding generation."""
        # Use docstring if available, otherwise intent summary
        doc = self.docstring or self.intent_summary or ""
        return f"{self.function_name} {doc}"
