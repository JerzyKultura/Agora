"""
Universal Code Ingestor - Embedding Generator

Generates semantic embeddings using sentence-transformers.
"""

import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Lazy import to avoid loading model unless needed
_model = None


def get_model():
    """Lazy-load sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)")
            _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            logger.info("✅ Model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
    return _model


class EmbeddingGenerator:
    """
    Generate semantic embeddings for code using sentence-transformers.
    
    Model: all-MiniLM-L6-v2 (384 dimensions)
    """
    
    def __init__(self):
        """Initialize embedding generator."""
        self.model = None
        self.dimension = 384
    
    def _ensure_model(self):
        """Ensure model is loaded."""
        if self.model is None:
            self.model = get_model()
    
    def generate(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            384-dimensional embedding vector
        """
        self._ensure_model()
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def batch_generate(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            List of embedding vectors
        """
        self._ensure_model()
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        return [emb.tolist() for emb in embeddings]
    
    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score in [0, 1]
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        similarity = np.dot(vec1, vec2) / (
            np.linalg.norm(vec1) * np.linalg.norm(vec2)
        )
        
        # Normalize to [0, 1]
        return (similarity + 1) / 2
