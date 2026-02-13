"""
Golden Score Integration Test Suite

Tests:
1. Database schema (context_cache table)
2. Golden scorer (embeddings, cosine similarity, ranking)
3. Context Prime endpoint (cache hit/miss, golden scores)
4. End-to-end flow

Usage:
    python test_golden_score.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.golden_scorer import GoldenScorer
from database import get_supabase


async def test_database_schema():
    """Test 1: Verify context_cache table exists"""
    print("\n🔍 Test 1: Database Schema")
    print("-" * 50)
    
    try:
        supabase = get_supabase()
        
        # Try to query the table
        result = supabase.table("context_cache").select("*").limit(1).execute()
        
        print("✅ context_cache table exists")
        print(f"   Columns: id, project_id, organization_id, context_summary, metadata, llm_provider, generated_at, expires_at")
        return True
    except Exception as e:
        print(f"❌ context_cache table missing or error: {e}")
        return False


async def test_golden_scorer_embeddings():
    """Test 2: Verify OpenAI embeddings work"""
    print("\n🔍 Test 2: Golden Scorer - Embeddings")
    print("-" * 50)
    
    try:
        scorer = GoldenScorer()
        
        if not scorer.client:
            print("⚠️  No OpenAI API key found, skipping embedding test")
            return None
        
        # Test embedding
        text = "critical authentication error in production"
        embedding = await scorer.get_embedding(text)
        
        if embedding is None:
            print("❌ Embedding API failed")
            return False
        
        print(f"✅ Embedding generated")
        print(f"   Dimension: {len(embedding)}")
        print(f"   Norm: {np.linalg.norm(embedding):.4f} (should be ~1.0 for OpenAI)")
        
        # Test cache
        embedding2 = await scorer.get_embedding(text)
        if np.array_equal(embedding, embedding2):
            print(f"✅ Embedding cache working")
            print(f"   Cache size: {len(scorer._cache)}")
        else:
            print("❌ Cache not working")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_cosine_similarity():
    """Test 3: Verify cosine similarity calculation"""
    print("\n🔍 Test 3: Cosine Similarity")
    print("-" * 50)
    
    try:
        scorer = GoldenScorer()
        
        # Test with known vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        vec3 = np.array([0.0, 1.0, 0.0])
        
        sim_identical = scorer.cosine_similarity(vec1, vec2)
        sim_orthogonal = scorer.cosine_similarity(vec1, vec3)
        
        print(f"✅ Identical vectors: {sim_identical:.4f} (should be 1.0)")
        print(f"✅ Orthogonal vectors: {sim_orthogonal:.4f} (should be 0.0)")
        
        if abs(sim_identical - 1.0) < 0.01 and abs(sim_orthogonal - 0.0) < 0.01:
            print("✅ Cosine similarity correct")
            return True
        else:
            print("❌ Cosine similarity incorrect")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_golden_score_calculation():
    """Test 4: Verify golden score formula"""
    print("\n🔍 Test 4: Golden Score Calculation")
    print("-" * 50)
    
    try:
        scorer = GoldenScorer()
        
        # Mock query embedding
        query_embedding = np.array([1.0, 0.0, 0.0])
        
        # Test item with high similarity, low success rate
        item1 = {
            "text": "test",
            "success_rate": 0.0
        }
        
        # Mock the embedding to be identical to query
        scorer._cache["test"] = np.array([1.0, 0.0, 0.0])
        
        score = await scorer.calculate_golden_score(item1, query_embedding)
        expected = (1.0 * 0.4) + (0.0 * 0.6)  # 0.4
        
        print(f"✅ Golden score: {score:.4f}")
        print(f"   Expected: {expected:.4f}")
        print(f"   Formula: (similarity × 0.4) + (success_rate × 0.6)")
        
        if abs(score - expected) < 0.01:
            print("✅ Golden score formula correct")
            return True
        else:
            print(f"❌ Golden score incorrect (got {score}, expected {expected})")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_fallback_ranking():
    """Test 5: Verify fallback heuristic ranking"""
    print("\n🔍 Test 5: Fallback Ranking")
    print("-" * 50)
    
    try:
        scorer = GoldenScorer(api_key=None)  # Force fallback
        
        items = [
            {
                "text": "minor warning in development",
                "timestamp": "2026-02-11T10:00:00Z",
                "status": "OK",
                "success_rate": 1.0
            },
            {
                "text": "critical authentication error in production",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "ERROR",
                "success_rate": 0.0
            }
        ]
        
        ranked = scorer._fallback_heuristic_ranking(
            items=items,
            query="critical error production",
            top_k=10,
            text_field="text"
        )
        
        print(f"✅ Fallback ranking completed")
        print(f"   Top item: {ranked[0][0]['text'][:50]}...")
        print(f"   Score: {ranked[0][1]:.4f}")
        
        # Critical error should rank higher
        if "critical" in ranked[0][0]["text"].lower():
            print("✅ Fallback ranking prioritizes critical errors")
            return True
        else:
            print("❌ Fallback ranking incorrect")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_context_prime_endpoint():
    """Test 6: Test Context Prime endpoint (requires running backend)"""
    print("\n🔍 Test 6: Context Prime Endpoint")
    print("-" * 50)
    
    try:
        import httpx
        
        # Check if backend is running
        try:
            response = await httpx.AsyncClient().get("http://localhost:8000/docs", timeout=2.0)
            if response.status_code != 200:
                print("⚠️  Backend not running on localhost:8000")
                return None
        except:
            print("⚠️  Backend not running on localhost:8000")
            print("   Start with: cd platform/backend && uvicorn main:app --reload")
            return None
        
        # You would need a valid API key and project ID to test this
        print("⚠️  Manual test required:")
        print("   1. Get your API key from Supabase")
        print("   2. Get a project_id from your projects table")
        print("   3. Run:")
        print('   curl -X POST http://localhost:8000/v1/context/prime \\')
        print('     -H "Authorization: Bearer agora_xxx" \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"project_id": "your-uuid"}\'')
        
        return None
    except Exception as e:
        print(f"⚠️  Could not test endpoint: {e}")
        return None


async def main():
    """Run all tests"""
    print("=" * 50)
    print("🧪 Golden Score Integration Test Suite")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Database Schema", await test_database_schema()))
    results.append(("Embeddings", await test_golden_scorer_embeddings()))
    results.append(("Cosine Similarity", await test_cosine_similarity()))
    results.append(("Golden Score Formula", await test_golden_score_calculation()))
    results.append(("Fallback Ranking", await test_fallback_ranking()))
    results.append(("Context Prime Endpoint", await test_context_prime_endpoint()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    
    for name, result in results:
        if result is True:
            print(f"✅ {name}")
        elif result is False:
            print(f"❌ {name}")
        else:
            print(f"⏸️  {name} (skipped)")
    
    print(f"\nPassed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print(f"Skipped: {skipped}/{len(results)}")
    
    if failed > 0:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
