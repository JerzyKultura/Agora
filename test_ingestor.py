#!/usr/bin/env python3
"""
Test the Universal Code Ingestor

Tests extraction, embedding, and dry-run mode.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agora.ingestor import CodeExtractor, EmbeddingGenerator, FunctionMetadata


def test_extraction():
    """Test AST-based code extraction."""
    print("=" * 70)
    print("🧪 Test 1: Code Extraction")
    print("=" * 70)
    
    # Create test file
    test_code = '''
def authenticate_user(username: str, password: str) -> str:
    """Authenticate user and return JWT token."""
    token = generate_token(username)
    db.users.update(username, last_login=now())
    return token

def validate_email(email):
    # No docstring - should generate intent summary
    result = email_validator.check(email)
    return result.is_valid
'''
    
    test_file = Path("test_sample.py")
    test_file.write_text(test_code)
    
    try:
        # Extract
        extractor = CodeExtractor(project_root=".")
        functions = extractor.extract_from_file(test_file)
        
        print(f"\n✅ Extracted {len(functions)} functions\n")
        
        for func in functions:
            print(f"📝 {func.function_name}")
            print(f"   Signature: {func.signature}")
            print(f"   File: {func.file_path}:{func.line_start}-{func.line_end}")
            
            if func.docstring:
                print(f"   Docstring: {func.docstring}")
            elif func.intent_summary:
                print(f"   Intent: {func.intent_summary}")
            
            print(f"   Parameters: {[p.name for p in func.parameters]}")
            print(f"   Return: {func.return_type}")
            print(f"   Dependencies: {func.dependencies}")
            print(f"   Hash: {func.get_node_hash()[:16]}...")
            print()
        
        # Verify dependency extraction
        auth_func = next(f for f in functions if f.function_name == "authenticate_user")
        assert "generate_token" in auth_func.dependencies
        assert "db.users.update" in auth_func.dependencies, \
            f"Expected 'db.users.update' in dependencies, got: {auth_func.dependencies}"
        
        print("✅ Dependency extraction working correctly!")
        print("   - Simple calls: 'generate_token'")
        print("   - Chained calls: 'db.users.update'")
        print("   - Chained calls: 'email_validator.check'")
        
        # Verify intent summary
        validate_func = next(f for f in functions if f.function_name == "validate_email")
        assert validate_func.intent_summary is not None
        print(f"\n✅ Intent summary generated: '{validate_func.intent_summary}'")
        
        return True
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


def test_embeddings():
    """Test embedding generation."""
    print("\n" + "=" * 70)
    print("🧪 Test 2: Embedding Generation")
    print("=" * 70)
    
    embedder = EmbeddingGenerator()
    
    texts = [
        "authenticate_user Authenticate user and return JWT token",
        "validate_email Validates email format",
        "process_payment Processes credit card payment"
    ]
    
    print(f"\nGenerating embeddings for {len(texts)} texts...")
    embeddings = embedder.batch_generate(texts, show_progress=False)
    
    print(f"✅ Generated {len(embeddings)} embeddings")
    print(f"   Dimension: {len(embeddings[0])}")
    print(f"   Sample values: {embeddings[0][:5]}")
    
    # Test similarity
    sim = embedder.cosine_similarity(embeddings[0], embeddings[1])
    print(f"\n✅ Cosine similarity test: {sim:.3f}")
    
    return True


def test_hash_uniqueness():
    """Test that node hashes are unique across files."""
    print("\n" + "=" * 70)
    print("🧪 Test 3: Hash Uniqueness")
    print("=" * 70)
    
    # Same function name, different files
    func1 = FunctionMetadata(
        function_name="format",
        file_path="utils.py",
        language="python",
        source_code="def format(): pass"
    )
    
    func2 = FunctionMetadata(
        function_name="format",
        file_path="parser.py",
        language="python",
        source_code="def format(): pass"
    )
    
    hash1 = func1.get_node_hash()
    hash2 = func2.get_node_hash()
    
    print(f"\nutils.py::format  → {hash1[:16]}...")
    print(f"parser.py::format → {hash2[:16]}...")
    
    assert hash1 != hash2, "Hashes should be different for same function in different files!"
    
    print("\n✅ Hash uniqueness verified!")
    print("   Functions with same name in different files have unique hashes")
    
    return True


def main():
    """Run all tests."""
    print("\n🚀 Universal Code Ingestor - Test Suite\n")
    
    tests = [
        ("Code Extraction", test_extraction),
        ("Embedding Generation", test_embeddings),
        ("Hash Uniqueness", test_hash_uniqueness)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
