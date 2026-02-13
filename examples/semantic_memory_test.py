"""
Semantic Memory Test - Golden Score Ranking

Tests the new semantic search system with:
1. Vector embeddings (sentence-transformers)
2. Golden Score ranking
3. Auto-migration from JSON
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agora.dev.codebase_analyzer import CodebaseAnalyzer
from agora.dev.node_generator import NodeGenerator
from agora.dev.context_manager import ContextManager

def main():
    print("🧠 Semantic Memory System Test\n")
    print("=" * 60)
    
    # Test 1: Check if semantic dependencies are available
    print("\n📦 Test 1: Dependency Check")
    print("-" * 60)
    
    try:
        from sentence_transformers import SentenceTransformer
        from vectordb import InMemoryExactNNVectorDB
        from docarray import BaseDoc, DocList
        print("✅ All semantic dependencies installed")
        semantic_available = True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("\nInstall with: pip install -e '.[semantic]'")
        semantic_available = False
        return
    
    # Test 2: Initialize ContextManager with semantic search
    print("\n\n� Test 2: Initialize Semantic ContextManager")
    print("-" * 60)
    
    session_id = "semantic_test"
    context = ContextManager(session_id, use_semantic=True)
    
    if context.use_semantic:
        print(f"✅ Semantic search enabled for session: {session_id}")
        print(f"📁 Storage: .agora/memory/{session_id}/")
    else:
        print("❌ Semantic search failed to initialize")
        return
    
    # Test 3: Save some test nodes with docstrings
    print("\n\n💾 Test 3: Save Test Nodes")
    print("-" * 60)
    
    test_nodes = [
        {
            "name": "authenticate_user",
            "code": "def authenticate_user(username, password): ...",
            "docstring": "Authenticate a user with username and password using JWT tokens",
            "tags": ["auth", "security"],
            "signature": "authenticate_user(username: str, password: str) -> bool"
        },
        {
            "name": "verify_token",
            "code": "def verify_token(token): ...",
            "docstring": "Verify JWT token validity and extract claims",
            "tags": ["auth", "validation"],
            "signature": "verify_token(token: str) -> dict"
        },
        {
            "name": "send_email",
            "code": "def send_email(to, subject, body): ...",
            "docstring": "Send an email notification to a user",
            "tags": ["notification", "email"],
            "signature": "send_email(to: str, subject: str, body: str) -> bool"
        },
        {
            "name": "process_payment",
            "code": "def process_payment(amount, card): ...",
            "docstring": "Process credit card payment through payment gateway",
            "tags": ["payment", "transaction"],
            "signature": "process_payment(amount: float, card: str) -> bool"
        },
        {
            "name": "validate_email",
            "code": "def validate_email(email): ...",
            "docstring": "Validate email address format using regex",
            "tags": ["validation", "email"],
            "signature": "validate_email(email: str) -> bool"
        }
    ]
    
    for node in test_nodes:
        context.save_node(
            node_name=node["name"],
            node_code=node["code"],
            tags=node["tags"],
            signature=node["signature"],
            docstring=node["docstring"]
        )
        print(f"  ✅ Saved: {node['name']}")
    
    # Test 4: Simulate usage to update success rates
    print("\n\n📊 Test 4: Simulate Node Usage")
    print("-" * 60)
    
    # authenticate_user: 10 uses, 9 successes (90%)
    for _ in range(9):
        context.record_node_outcome("authenticate_user", success=True)
    context.record_node_outcome("authenticate_user", success=False)
    print("  authenticate_user: 90% success rate (9/10)")
    
    # verify_token: 5 uses, 5 successes (100%)
    for _ in range(5):
        context.record_node_outcome("verify_token", success=True)
    print("  verify_token: 100% success rate (5/5)")
    
    # send_email: 8 uses, 4 successes (50%)
    for _ in range(4):
        context.record_node_outcome("send_email", success=True)
    for _ in range(4):
        context.record_node_outcome("send_email", success=False)
    print("  send_email: 50% success rate (4/8)")
    
    # process_payment: 3 uses, 1 success (33%)
    context.record_node_outcome("process_payment", success=True)
    context.record_node_outcome("process_payment", success=False)
    context.record_node_outcome("process_payment", success=False)
    print("  process_payment: 33% success rate (1/3)")
    
    # validate_email: new node (default 50%)
    print("  validate_email: 50% success rate (default, no usage)")
    
    # Test 5: Semantic Search with Golden Score
    print("\n\n🔍 Test 5: Semantic Search (Golden Score Ranking)")
    print("-" * 60)
    
    queries = [
        "user login authentication",
        "email validation",
        "payment processing",
        "JWT token"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        results = context.search_nodes(query, top_k=3)
        
        for i, (node, golden_score) in enumerate(results, 1):
            # Calculate components
            success_rate = 0.5
            if node.usage_count > 0:
                success_rate = node.success_count / node.usage_count
            
            # Reverse-engineer cosine similarity from golden score
            # golden_score = (cosine * 0.4) + (success_rate * 0.6)
            # cosine = (golden_score - success_rate * 0.6) / 0.4
            cosine_sim = (golden_score - success_rate * 0.6) / 0.4
            
            print(f"  {i}. {node.name}")
            print(f"     Golden Score: {golden_score:.3f}")
            print(f"       ├─ Cosine Similarity: {cosine_sim:.3f} (×0.4 = {cosine_sim * 0.4:.3f})")
            print(f"       └─ Success Rate: {success_rate:.3f} (×0.6 = {success_rate * 0.6:.3f})")
    
    # Test 6: Grep Search (Exact Match)
    print("\n\n🔎 Test 6: Grep Search (Exact String Match)")
    print("-" * 60)
    
    grep_query = "verify"
    print(f"\nGrep: '{grep_query}'")
    results = context.search_nodes(grep_query, top_k=5, use_grep=True)
    
    for i, (node, score) in enumerate(results, 1):
        print(f"  {i}. {node.name} (exact match)")
    
    # Test 7: Compare Semantic vs Keyword
    print("\n\n⚖️  Test 7: Semantic vs Keyword Comparison")
    print("-" * 60)
    
    # Create a non-semantic context for comparison
    context_legacy = ContextManager(session_id + "_legacy", use_semantic=False)
    
    # Save same nodes to legacy
    for node in test_nodes:
        context_legacy.save_node(
            node_name=node["name"],
            node_code=node["code"],
            tags=node["tags"],
            signature=node["signature"],
            docstring=node["docstring"]
        )
    
    test_query = "login security"
    
    print(f"\nQuery: '{test_query}'")
    print("\nSemantic Results:")
    semantic_results = context.search_nodes(test_query, top_k=3)
    for i, (node, score) in enumerate(semantic_results, 1):
        print(f"  {i}. {node.name} (Score: {score:.3f})")
    
    print("\nKeyword Results:")
    keyword_results = context_legacy.search_nodes(test_query, top_k=3)
    for i, (node, score) in enumerate(keyword_results, 1):
        print(f"  {i}. {node.name} (Score: {score:.3f})")
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📈 Summary")
    print("=" * 60)
    
    summary = context.get_summary()
    print(f"\nSession: {summary['session_id']}")
    print(f"Total Nodes: {summary['total_nodes']}")
    print(f"Total Executions: {summary['total_executions']}")
    print(f"Overall Success Rate: {summary['success_rate']:.1%}")
    print(f"Semantic Enabled: {summary['semantic_enabled']}")
    
    print("\n✅ All tests completed!")
    print(f"\n📁 Data stored in:")
    print(f"   Vector DB: .agora/memory/{session_id}/")
    print(f"   Legacy JSON: .agora/sessions/{session_id}_legacy/")


if __name__ == "__main__":
    main()
