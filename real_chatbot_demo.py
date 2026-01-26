#!/usr/bin/env python3
"""
REAL-WORLD CHATBOT DEMO: Mem0 + Zilliz + Agora
--------------------------------------------------
This script demonstrates a production-ready AI pipeline.
If real libraries are missing, it falls back to mocks.

Setup for Google Colab:
---------------------
!pip install agora-py mem0ai pymilvus openai python-dotenv

# Set your keys:
import os
os.environ["AGORA_API_KEY"] = "sk-..."
os.environ["VITE_SUPABASE_URL"] = "https://your-project.supabase.co"
os.environ["VITE_SUPABASE_ANON_KEY"] = "..."
os.environ["OPENAI_API_KEY"] = "sk-..."
os.environ["MEM0_API_KEY"] = "..."
os.environ["QDRANT_URL"] = "https://your-cluster.qdrant.io"
os.environ["QDRANT_API_KEY"] = "your-api-key"
--------------------------------------------------
"""

import asyncio
import os
import warnings
import sys

# 0. Clean up the output (silence DeprecationWarnings from old packages)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 1. SETUP YOUR KEYS: Load from .env first!
# --------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed. Skipping .env load.")

# Helper to ensure we don't overwrite real env vars with demo placeholders
def set_if_missing(key, value):
    if not os.environ.get(key) and value != "...":
        os.environ[key] = value

# Default placeholders (won't overwrite if you have a .env file!)
set_if_missing("AGORA_API_KEY", "sk-placeholder") 
set_if_missing("VITE_SUPABASE_URL", "https://your-project.supabase.co")
set_if_missing("VITE_SUPABASE_ANON_KEY", "...") 
set_if_missing("OPENAI_API_KEY", "sk-your-key-here")
set_if_missing("MEM0_API_KEY", "...")
set_if_missing("QDRANT_URL", "your-qdrant-url")
set_if_missing("QDRANT_API_KEY", "your-qdrant-key")
# --------------------------------------------------

from agora.agora_tracer import init_agora, agora_node, TracedAsyncFlow

# 2. Check for missing keys and provide feedback
def verify_setup():
    print("\n" + "🔍 Verifying Environment".center(60, "-"))
    if os.environ.get("OPENAI_API_KEY") == "sk-your-key-here":
        print("⚠️  OPENAI_API_KEY is not set. Real Mem0 will be DISABLED (Mocking instead).")
        return False
    print("✅ OpenAI Key detected.")
    return True

SETUP_IS_REAL = verify_setup()

# 3. Initialize Agora
init_agora(
    app_name="talking-chatbot",
    project_name="Production Chatbot",
    export_to_console=False
)

# 4. Try imports for Real Tools
try:
    # Only use real Mem0 if we have an OpenAI Key and the lib
    if SETUP_IS_REAL:
        from mem0 import Memory
        HAS_MEM0 = True
    else:
        HAS_MEM0 = False
except ImportError:
    HAS_MEM0 = False

try:
    from pymilvus import MilvusClient
    HAS_ZILLIZ = True
except ImportError:
    HAS_ZILLIZ = False

try:
    from qdrant_client import QdrantClient
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False

# Setup Environment Variables (Self-Correction/Detection)
# export QDRANT_URL="..."
# export QDRANT_API_KEY="..."

# --- Advanced Retrieval Logic ---

@agora_node(name="MemoryRetrieval")
async def retrieve_memory(shared):
    from opentelemetry import trace
    span = trace.get_current_span()

    user_id = shared.get("user_id", "default_user")
    print(f"🧠 Checking Mem0 history for {user_id}...")
    
    if HAS_MEM0 and os.environ.get("OPENAI_API_KEY") != "sk-your-key-here":
        # REAL Mem0 call
        m = Memory()
        history = m.search(shared["query"], user_id=user_id)
        
        # BOOTSTRAP: Add a first memory if history is empty
        if not history or (isinstance(history, list) and len(history) == 0):
            print("✨ Mem0 is empty. Adding your first memory...")
            m.add("User is exploring Agora's brand new telemetry platform.", user_id=user_id)
            history = m.search(shared["query"], user_id=user_id)
            
        shared["memory_context"] = history
    else:
        # MOCK fallback for safety
        await asyncio.sleep(0.5)
        shared["memory_context"] = ["User likes efficient telemetry."]
    
    # TELEMETRY: Explicitly record what was retrieved on the span
    if span and span.is_recording():
        span.set_attribute("memory.retrieved_chunks", str(shared["memory_context"]))
        span.set_attribute("memory.user_id", user_id)
    
    return "search"

@agora_node(name="VectorSearch")
async def vector_search(shared):
    """
    FREE TIER TIP: Use Milvus Lite (local file) or Qdrant (:memory:)!
    """
    from opentelemetry import trace
    span = trace.get_current_span()

    print(f"🔍 Searching Vector DB...")
    
    # Priority: Qdrant Cluster -> Zilliz Cloud -> Milvus Lite (Local)
    qdrant_url = os.environ.get("QDRANT_URL")
    zilliz_uri = os.environ.get("ZILLIZ_CLOUD_URI")
    vector_provider = "unknown"
    
    # Matching User's Cluster: 512 Dimensions
    dummy_vector = [0.1] * 512 
    
    results_payload = []

    if qdrant_url and HAS_QDRANT:
        print(f"Using Qdrant Cluster at {qdrant_url}...")
        vector_provider = "qdrant"
        try:
            client = QdrantClient(
                url=qdrant_url, 
                api_key=os.environ.get("QDRANT_API_KEY")
            )
            
            # MODERN QDRANT API: query_points
            if hasattr(client, "query_points"):
                # BOOTSTRAP: If collection is empty, let's add something!
                try:
                    count = client.count(collection_name="agora_collection").count
                    if count == 0:
                        print("✨ Collection is empty. Bootstrapping with demo knowledge...")
                        client.upsert(
                            collection_name="agora_collection",
                            points=[{
                                "id": 1,
                                "vector": dummy_vector,
                                "payload": {"text": "Agora is a self-hosted telemetry platform for Python workflows."}
                            }]
                        )
                except: pass

                results = client.query_points(
                    collection_name="agora_collection",
                    query=dummy_vector,
                    limit=1
                ).points
                results_payload = [str(r.payload.get("text") or r) for r in results]
                shared["search_results"] = results_payload
            # CLASSIC QDRANT API: search
            elif hasattr(client, "search"):
                results = client.search(
                    collection_name="agora_collection",
                    query_vector=dummy_vector,
                    limit=1
                )
                results_payload = [str(r) for r in results]
                shared["search_results"] = results_payload
            else:
                shared["search_results"] = ["Compatible Qdrant search method not found."]
        except Exception as e:
            print(f"Qdrant search error: {e}")
            shared["search_results"] = [f"Qdrant query failed: {str(e)}"]
            
    elif zilliz_uri and HAS_ZILLIZ:
        print("Using Zilliz Cloud...")
        vector_provider = "zilliz"
        client = MilvusClient(uri=zilliz_uri, token=os.environ.get("ZILLIZ_CLOUD_API_KEY"))
        results = client.search(collection_name="agora_collection", data=[dummy_vector], limit=1)
        results_payload = [str(r) for r in results]
        shared["search_results"] = results_payload
        
    elif HAS_ZILLIZ:
        print("Using Milvus Lite (local)...")
        vector_provider = "milvus-lite"
        client = MilvusClient(uri="agora_local.db")
        if not client.has_collection("agora_collection"):
            client.create_collection("agora_collection", dimension=512)
            client.insert("agora_collection", [{"vector": dummy_vector}])
        results = client.search(collection_name="agora_collection", data=[dummy_vector], limit=1)
        results_payload = [str(r) for r in results]
        shared["search_results"] = results_payload
    else:
        # MOCK fallback
        vector_provider = "mock"
        await asyncio.sleep(0.7)
        results_payload = ["Agora uses OTel standards (Free Tier Mock)."]
        shared["search_results"] = results_payload
    
    # TELEMETRY: Record vector DB details
    if span and span.is_recording():
        span.set_attribute("vector_db.provider", vector_provider)
        span.set_attribute("vector_db.results_count", len(results_payload))
        # Store actual chunks to visualize content!
        span.set_attribute("vector_db.retrieved_chunks", str(results_payload))

    return "generate"

@agora_node(name="SynthesizeResponse")
async def synthesize(shared):
    print(f"🤖 Synthesizing answer...")
    await asyncio.sleep(1.0) # Simulate LLM
    
    # ULTIMA SAFETY: Force clear strings even for nested empties
    def parse_result(val, default):
        if not val or str(val).strip() in ["[]", "{}", "[[]]", "None", "()"]: 
            return default
            
        if isinstance(val, list) and len(val) > 0:
            item = val[0]
            if isinstance(item, list) and len(item) == 0: return default
            if isinstance(item, dict) and len(item) == 0: return default
            return str(item)
            
        if isinstance(val, dict) and len(val) > 0:
            return str(list(val.values())[0])
            
        return str(val)

    memory_str = parse_result(shared.get("memory_context"), "New user with fresh history")
    search_str = parse_result(shared.get("search_results"), "Agora is a telemetry platform")
    
    response = f"Based on your memory ({memory_str}), Agora works well because {search_str}."
    shared["response"] = response
    return None

async def main():
    flow = TracedAsyncFlow("TalkingChatbot")
    flow.start(retrieve_memory)

    # Define Graph
    retrieve_memory - "search" >> vector_search
    vector_search - "generate" >> synthesize

    # Run Execution
    print("\n" + "🚀 Starting Real-World Demo".center(60, "="))
    shared = {"query": "Tell me about Agora's standards", "user_id": "user_456"}
    await flow.run_async(shared)
    print("="*60 + "\n")
    print(f"✨ AI: {shared['response']}")
    print("\n✅ Check your Agora dashboard! You should see the '🔑 Agora API Key verified' log above.")

if __name__ == "__main__":
    import sys
    is_notebook = 'ipykernel' in sys.modules or 'google.colab' in sys.modules

    if is_notebook:
        print("\n" + "🚀 READY FOR EXECUTION (Colab/Jupyter)".center(60, "-"))
        print("To see the full trace and AI response, run this in the next cell:")
        print("\nawait main()\n")
        print("-" * 60)
    else:
        asyncio.run(main())
