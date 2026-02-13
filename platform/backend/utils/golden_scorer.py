"""
Golden Scorer - Golden Score ranking for Context Prime

Uses OpenAI text-embedding-3-small for semantic similarity.
Golden Score = (CosineSimilarity × 0.4) + (SuccessRate × 0.6)

Supports BYOK (org key → system key → fallback).
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import numpy as np
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class GoldenScorer:
    """
    Ranks items by golden score using semantic embeddings.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with OpenAI API key.
        
        Args:
            api_key: OpenAI API key (org BYOK or system key)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "text-embedding-3-small"
        self._cache: Dict[str, np.ndarray] = {}
        self._cache_max_size = 100
    
    async def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding vector for text with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embedding or None if failed
        """
        if text in self._cache:
            return self._cache[text]
        
        if not self.client:
            return None
        
        try:
            response = await asyncio.wait_for(
                self.client.embeddings.create(
                    model=self.model,
                    input=text
                ),
                timeout=5.0
            )
            
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else len(text.split())
            logger.info(f"Embedding tokens: {tokens_used} for text length {len(text)}")
            
            embedding = np.array(response.data[0].embedding)
            
            if len(self._cache) < self._cache_max_size:
                self._cache[text] = embedding
            
            return embedding
        except asyncio.TimeoutError:
            logger.error("Embedding API timeout (5s)")
            return None
        except Exception as e:
            logger.error(f"Embedding API error: {e}")
            return None
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score in [0, 1]
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, similarity)
    
    async def calculate_golden_score(
        self,
        item: Dict[str, Any],
        query_embedding: np.ndarray,
        text_field: str = "text"
    ) -> float:
        """
        Calculate golden score for an item.
        
        Golden Score = (CosineSimilarity × 0.4) + (SuccessRate × 0.6)
        
        Args:
            item: Item dict with text and optional success_rate
            query_embedding: Pre-computed query embedding
            text_field: Field name containing text to embed
            
        Returns:
            Golden score in [0, 1]
        """
        text = item.get(text_field, "")
        if not text:
            return 0.0
        
        item_embedding = await self.get_embedding(text)
        if item_embedding is None:
            return 0.5
        
        similarity = self.cosine_similarity(query_embedding, item_embedding)
        success_rate = item.get("success_rate", 0.5)
        
        golden_score = (similarity * 0.4) + (success_rate * 0.6)
        return golden_score
    
    async def rank_by_salience(
        self,
        items: List[Dict[str, Any]],
        query: str,
        top_k: int = 10,
        text_field: str = "text"
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank items by golden score.
        
        Args:
            items: List of items to rank
            query: Query string for semantic relevance
            top_k: Number of top results to return
            text_field: Field name containing text to embed
            
        Returns:
            List of (item, golden_score) tuples, sorted descending
        """
        if not items:
            return []
        
        query_embedding = await self.get_embedding(query)
        if query_embedding is None:
            return self._fallback_heuristic_ranking(items, query, top_k, text_field)
        
        scored_items = []
        for item in items:
            score = await self.calculate_golden_score(item, query_embedding, text_field)
            scored_items.append((item, score))
        
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return scored_items[:top_k]
    
    def _fallback_heuristic_ranking(
        self,
        items: List[Dict[str, Any]],
        query: str,
        top_k: int,
        text_field: str
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Fallback to heuristic ranking if embeddings unavailable.
        
        Scoring:
        - Recency (40%): Decay over 24 hours
        - Severity (30%): ERROR status or low success rate
        - Keyword match (30%): Query words in text
        
        Args:
            items: List of items to rank
            query: Query string
            top_k: Number of results
            text_field: Field name containing text
            
        Returns:
            List of (item, score) tuples
        """
        scored_items = []
        query_words = set(query.lower().split())
        
        for item in items:
            score = 0.0
            
            if "timestamp" in item and item["timestamp"]:
                try:
                    timestamp = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                    age_hours = (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600
                    recency = max(0, 1.0 - (age_hours / 24))
                    score += recency * 0.4
                except Exception:
                    score += 0.2
            else:
                score += 0.2
            
            if item.get("status") == "ERROR" or item.get("success_rate", 1.0) < 0.5:
                score += 0.3
            
            text = item.get(text_field, "").lower()
            text_words = set(text.split())
            matches = len(query_words & text_words)
            if matches > 0:
                keyword_score = min(matches / len(query_words), 1.0)
                score += keyword_score * 0.3
            
            scored_items.append((item, min(score, 1.0)))
        
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return scored_items[:top_k]
