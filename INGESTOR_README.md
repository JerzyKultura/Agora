# Universal Code Ingestor

**Transform any Python codebase into a searchable, AI-queryable knowledge base.**

The Universal Code Ingestor scans raw Python codebases (no decorators required), extracts functions with rich metadata, generates semantic embeddings, and syncs everything to Supabase for intelligent search.

## 🎯 Features

- **AST-Based Extraction**: Parse any Python codebase without modifications
- **Dependency Graph**: Captures full call chains (`db.users.get`, not just `get`)
- **Intent Summaries**: Auto-generates descriptions for undocumented functions
- **Semantic Search**: 384-dim embeddings via sentence-transformers
- **Supabase Sync**: Batched upserts with telemetry preservation
- **Modular Design**: BaseStorage abstraction for easy backend swapping
- **Error Tolerant**: Gracefully handles syntax errors and continues

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -e '.[semantic]'
pip install supabase python-dotenv
```

### 2. Configure Supabase Credentials

Add to your `.env` file:

```bash
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_SERVICE_KEY="your-service-role-key"
```

> **Note**: Get your service role key from Supabase Dashboard → Settings → API

### 3. Set Up Supabase Table

Run the migration in Supabase SQL Editor:

```sql
-- Copy and run: supabase/migrations/create_knowledge_base.sql
```

### 4. Ingest Your Codebase

```bash
# Dry run (see what would be synced)
python3 ingest_codebase.py /path/to/your/codebase --dry-run

# Actually sync to Supabase
python3 ingest_codebase.py /path/to/your/codebase
```

## 📊 Example Output

```
======================================================================
🚀 Starting Universal Code Ingestor
======================================================================
Project Root: /Users/you/project
Dry Run: False

📂 Step 1: Extracting functions from codebase...
✅ Extracted 247 functions

🧠 Step 2: Generating semantic embeddings...
Batches: 100%|████████| 8/8 [00:03<00:00,  2.31it/s]
✅ Generated 247 embeddings

☁️  Step 3: Syncing to Supabase...
Upserted batch 1: 50 nodes
Upserted batch 2: 50 nodes
Upserted batch 3: 50 nodes
Upserted batch 4: 50 nodes
Upserted batch 5: 47 nodes
✅ Synced 247 functions to Supabase

======================================================================
📊 Ingestion Complete!
======================================================================
Total Functions: 247
Synced: 247
Errors: 0
======================================================================
```

## 🔍 What Gets Extracted

For each function, the ingestor captures:

```python
{
  "function_name": "authenticate_user",
  "signature": "authenticate_user(username: str, password: str) -> str",
  "file_path": "backend/auth/handlers.py",
  "line_start": 42,
  "line_end": 58,
  
  "docstring": "Authenticate user and return JWT token",
  "intent_summary": null,  # Only if no docstring
  
  "parameters": [
    {"name": "username", "type_hint": "str", "is_required": true},
    {"name": "password", "type_hint": "str", "is_required": true}
  ],
  "return_type": "str",
  
  "dependencies": [
    "generate_token",
    "db.users.update",  # Full call chains!
    "validate_credentials"
  ],
  
  "embedding": [0.038, -0.042, ...],  # 384-dim vector
  "node_hash": "a3f2e1...",  # Unique: sha256(file_path + name + language)
  
  "usage_count": 0,
  "success_rate": 0.5
}
```

## 🧠 Semantic Search

Query your codebase from Supabase:

```python
from supabase import create_client
import numpy as np
from sentence_transformers import SentenceTransformer

# Setup
supabase = create_client(url, key)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Generate query embedding
query = "authenticate user with JWT"
query_embedding = model.encode(query).tolist()

# Search
results = supabase.rpc('search_knowledge_base', {
    'query_embedding': query_embedding,
    'match_threshold': 0.7,  # Adjust for quality
    'match_count': 10
}).execute()

for row in results.data:
    print(f"{row['function_name']} - {row['file_path']}")
    print(f"  Similarity: {row['similarity']:.3f}")
    print(f"  {row['docstring']}")
```

## 🎛️ CLI Options

```bash
python3 ingest_codebase.py <directory> [OPTIONS]

Options:
  --supabase-url URL       Supabase project URL
  --supabase-key KEY       Supabase service key
  --exclude PATTERN        Patterns to exclude (e.g., test_* migrations)
  --dry-run                Show what would be synced without syncing
  --verbose                Enable debug logging
```

## 🏗️ Architecture

```
agora/ingestor/
├── models.py              # FunctionMetadata, ParameterInfo
├── storage.py             # BaseStorage (abstract interface)
├── extractor.py           # AST-based code extraction
├── embeddings.py          # Sentence-transformers integration
└── supabase_storage.py    # Supabase backend implementation

ingest_codebase.py         # Standalone CLI script
test_ingestor.py           # Test suite
```

### Modular Storage

The `BaseStorage` interface makes it easy to add new backends:

```python
from agora.ingestor import BaseStorage, FunctionMetadata

class LocalStorage(BaseStorage):
    """SQLite + JSON storage (coming soon)"""
    
    def connect(self): ...
    def upsert_node(self, node): ...
    def batch_upsert(self, nodes): ...
    def search_semantic(self, embedding): ...
```

## 🔧 Advanced Features

### Intent Summaries

Functions without docstrings get auto-generated summaries:

```python
def get_user_profile(user_id):
    # No docstring
    return db.users.find(user_id)

# Intent: "Retrieves user profile"
```

### Dependency Depth

Full attribute chains are captured:

```python
def process_order(order_id):
    order = db.orders.find(order_id)  # → "db.orders.find"
    payment = stripe.charges.create()  # → "stripe.charges.create"
    notify_user(order.user_id)         # → "notify_user"
```

### Hash Uniqueness

Functions with the same name in different files get unique hashes:

```python
# utils.py::format → hash_1
# parser.py::format → hash_2
```

Hash = `sha256(file_path + function_name + language)`

### Telemetry Preservation

On re-ingestion, usage stats are preserved:

```python
# First ingest: usage_count=0, success_rate=0.5
# After 10 uses: usage_count=10, success_rate=0.9
# Re-ingest (code updated): usage_count=10, success_rate=0.9 ✅
```

## 📝 Supabase Schema

Key fields in `agora_knowledge_base`:

- `node_hash` (TEXT, UNIQUE): Deduplication key
- `embedding` (VECTOR(384)): Semantic search vector
- `dependencies` (JSONB): Full call paths
- `usage_count`, `success_rate`: Telemetry
- Vector index: IVFFlat for fast similarity search

## 🧪 Testing

```bash
# Run test suite
python3 test_ingestor.py

# Tests:
# ✅ Code extraction with dependency graphs
# ✅ Embedding generation (384-dim)
# ✅ Hash uniqueness across files
# ✅ Intent summary generation
```

## 🎯 Use Cases

1. **AI Code Search**: Let agents find relevant functions semantically
2. **Documentation Generation**: Auto-document undocumented code
3. **Dependency Analysis**: Understand call graphs
4. **Code Migration**: Track function usage before refactoring
5. **Knowledge Base**: Make your codebase queryable by LLMs

## 🔒 Security

- Use `SUPABASE_SERVICE_KEY` (not anon key) for write access
- Set RLS policies on `agora_knowledge_base` table
- Never commit credentials to git

## 📚 Next Steps

1. **Ingest your codebase**: `python3 ingest_codebase.py .`
2. **Query from your website**: Use the `search_knowledge_base` RPC
3. **Add to AI agents**: Provide context from your codebase
4. **Track usage**: Update `usage_count` and `success_rate` as functions are used

---

**Built with ❤️ for the Agora Platform**
