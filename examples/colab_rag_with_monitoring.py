"""
Google Colab RAG Chat Demo with Agora Monitoring Platform Integration

This example demonstrates:
1. RAG chat app with Qdrant vector database
2. OpenTelemetry spans auto-instrumented by Traceloop
3. Business context (wide events) enriching all spans
4. Full visibility in Agora monitoring platform at localhost:5173

Copy-paste this into Google Colab and run!
"""

# ============================================================================
# CELL 1: Install Dependencies
# ============================================================================
"""
!pip install -q agora-ai openai qdrant-client traceloop-sdk supabase python-dotenv
"""

# ============================================================================
# CELL 2: Credentials Setup
# ============================================================================
"""
import os
from getpass import getpass

# Option 1: Use getpass for secure input (recommended)
print("Please enter your credentials:")
os.environ['OPENAI_API_KEY'] = getpass('OpenAI API Key: ')
os.environ['QDRANT_API_KEY'] = getpass('Qdrant API Key: ')
os.environ['QDRANT_URL'] = input('Qdrant URL: ')
os.environ['VITE_SUPABASE_URL'] = input('Supabase URL: ')
os.environ['VITE_SUPABASE_ANON_KEY'] = getpass('Supabase Anon Key: ')

# Option 2: Or set them directly (NOT RECOMMENDED for sharing)
# os.environ['OPENAI_API_KEY'] = 'sk-...'
# os.environ['QDRANT_API_KEY'] = 'your-qdrant-key'
# os.environ['QDRANT_URL'] = 'https://your-qdrant-url'
# os.environ['VITE_SUPABASE_URL'] = 'https://your-supabase-url.supabase.co'
# os.environ['VITE_SUPABASE_ANON_KEY'] = 'eyJ...'

# Optional: Project ID (if you want to associate with a specific project)
# os.environ['AGORA_PROJECT_ID'] = 'your-project-uuid-here'

print("✅ Credentials configured!")
"""

# ============================================================================
# CELL 3: RAG Chat with Full Monitoring
# ============================================================================

import os
import asyncio
import uuid
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Import Agora telemetry
from agora.agora_tracer import init_agora
from agora.wide_events import set_business_context, BusinessContext

# ============================================================================
# CONFIGURATION
# ============================================================================

COLLECTION_NAME = "agora_docs"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
EMBEDDING_DIMENSIONS = 1536
RETRIEVAL_K = 3

# ============================================================================
# INITIALIZE AGORA TELEMETRY
# ============================================================================

print("🚀 Initializing Agora telemetry...")

# Initialize with Supabase upload enabled
init_agora(
    app_name="colab-rag-chat",
    export_to_console=False,  # Set to True if you want to see spans in console
    enable_cloud_upload=True,  # Upload to Supabase for monitoring platform
    supabase_url=os.environ.get('VITE_SUPABASE_URL'),
    supabase_key=os.environ.get('VITE_SUPABASE_ANON_KEY'),
    project_id=os.environ.get('AGORA_PROJECT_ID')  # Optional
)

print("✅ Agora telemetry initialized!\n")

# ============================================================================
# SET BUSINESS CONTEXT (Wide Events)
# ============================================================================
# This context will be automatically added to ALL OpenTelemetry spans!
# No need to manually enrich each span - it's plug-and-play!

session_id = f"chat_{int(time.time())}"
user_id = "demo_user_123"
subscription_tier = "pro"

print(f"👤 User: {user_id}")
print(f"🎫 Subscription: {subscription_tier}")
print(f"📊 Session: {session_id}\n")

# Set business context ONCE - all spans will inherit this!
set_business_context(
    user_id=user_id,
    subscription_tier=subscription_tier,
    session_id=session_id,
    workflow_type="rag_chat",
    app_version="1.0.0",
    custom={
        "qdrant_collection": COLLECTION_NAME,
        "embedding_model": EMBEDDING_MODEL,
        "chat_model": CHAT_MODEL,
        "retrieval_k": RETRIEVAL_K
    }
)

print("✅ Business context set! All LLM calls will be enriched automatically.\n")

# ============================================================================
# INITIALIZE CLIENTS
# ============================================================================

print("🔧 Initializing OpenAI and Qdrant clients...")
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
qdrant_client = QdrantClient(
    url=os.environ['QDRANT_URL'],
    api_key=os.environ['QDRANT_API_KEY']
)

# ============================================================================
# CREATE QDRANT COLLECTION & SEED DATA
# ============================================================================

print(f"📦 Setting up Qdrant collection: {COLLECTION_NAME}...")

# Recreate collection (fresh start)
try:
    qdrant_client.delete_collection(COLLECTION_NAME)
    print(f"  🗑️  Deleted existing collection")
except:
    pass

qdrant_client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=EMBEDDING_DIMENSIONS, distance=Distance.COSINE)
)
print(f"  ✅ Created collection with {EMBEDDING_DIMENSIONS}D vectors")

# Seed knowledge base
docs = [
    "Agora is an AI workflow orchestration framework for building production-grade LLM applications.",
    "Agora provides built-in observability with OpenTelemetry integration and a web-based monitoring platform.",
    "To use Agora, create nodes by subclassing AsyncNode and implement the exec_async method.",
    "Agora supports retry logic, error handling, and distributed tracing out of the box.",
    "The Agora monitoring platform displays LLM spans, token usage, costs, and business context at localhost:5173."
]

print(f"  📝 Embedding {len(docs)} documents...")
for i, doc in enumerate(docs):
    # This embedding call is auto-instrumented by Traceloop!
    # Business context is automatically added to the span!
    embedding_response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=doc
    )
    vector = embedding_response.data[0].embedding

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=i, vector=vector, payload={"text": doc})]
    )

print(f"  ✅ Uploaded {len(docs)} documents to Qdrant\n")

# ============================================================================
# RAG HELPER FUNCTION
# ============================================================================

def rag_chat(user_query: str, conversation_turn: int) -> str:
    """
    RAG chat function that:
    1. Embeds the user query (auto-traced)
    2. Retrieves relevant docs from Qdrant (auto-traced)
    3. Generates response with OpenAI (auto-traced)

    All spans automatically include business context!
    """

    # Update conversation turn in business context
    set_business_context(
        user_id=user_id,
        subscription_tier=subscription_tier,
        session_id=session_id,
        conversation_turn=conversation_turn,
        workflow_type="rag_chat",
        app_version="1.0.0",
        custom={
            "qdrant_collection": COLLECTION_NAME,
            "embedding_model": EMBEDDING_MODEL,
            "chat_model": CHAT_MODEL,
            "retrieval_k": RETRIEVAL_K,
            "user_query": user_query  # High-cardinality field for debugging
        }
    )

    # 1. Embed query (auto-traced with business context!)
    query_embedding = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=user_query
    ).data[0].embedding

    # 2. Retrieve from Qdrant (auto-traced with business context!)
    search_results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=RETRIEVAL_K
    ).points

    # Extract retrieved text
    retrieved_docs = [hit.payload["text"] for hit in search_results]
    context = "\n".join(retrieved_docs)

    # 3. Generate response (auto-traced with business context!)
    messages = [
        {"role": "system", "content": f"You are a helpful assistant. Use the following context to answer questions:\n\n{context}"},
        {"role": "user", "content": user_query}
    ]

    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=200
    )

    answer = response.choices[0].message.content
    return answer

# ============================================================================
# INTERACTIVE CHAT LOOP
# ============================================================================

print("=" * 70)
print("💬 RAG CHAT DEMO - Type 'exit' to quit")
print("=" * 70)
print()

# Demo queries
demo_queries = [
    "What is Agora?",
    "How do I use it?",
    "Where can I see the monitoring data?"
]

for turn, query in enumerate(demo_queries, start=1):
    print(f"{'─' * 70}")
    print(f"Turn {turn}/{len(demo_queries)}")
    print(f"{'─' * 70}")
    print(f"👤 User: {query}")

    # Call RAG function (all LLM calls auto-traced with business context!)
    answer = rag_chat(query, conversation_turn=turn)

    print(f"🤖 Assistant: {answer}")
    print()

print("=" * 70)
print("✅ Chat demo complete!")
print("=" * 70)
print()

# ============================================================================
# FLUSH TELEMETRY & SHOW MONITORING INFO
# ============================================================================

print("📤 Flushing telemetry to Supabase...")

# Get cloud uploader to flush spans
import agora.agora_tracer as agora_module
cloud_uploader = getattr(agora_module, 'cloud_uploader', None)

if cloud_uploader:
    # Flush any pending spans
    await cloud_uploader.flush_spans()

    # Mark execution as complete
    execution_id = cloud_uploader.execution_id
    if execution_id:
        await cloud_uploader.complete_execution(status="success")

        print(f"✅ Telemetry uploaded successfully!")
        print()
        print("=" * 70)
        print("🎯 VIEW YOUR DATA IN THE MONITORING PLATFORM")
        print("=" * 70)
        print()
        print(f"📊 Execution ID: {execution_id}")
        print(f"👤 User ID: {user_id}")
        print(f"📞 Session ID: {session_id}")
        print(f"🎫 Subscription: {subscription_tier}")
        print()
        print("🌐 Open monitoring UI: http://localhost:5173/")
        print()
        print("To view your execution:")
        print("  1. Click 'Monitoring' in the left sidebar")
        print("  2. Switch to 'Traces' view")
        print(f"  3. Search for session ID: {session_id}")
        print("  4. Or search for user ID: {user_id}")
        print("  5. Click on a trace to see:")
        print("     - Full conversation (Messages tab)")
        print("     - Token usage & costs (LLM Data tab)")
        print("     - Business context (Details tab)")
        print("     - Waterfall visualization (Trace tab)")
        print()
        print("All your LLM calls, embeddings, and Qdrant searches are captured!")
        print("Business context is visible in the 'Details' and 'Raw' tabs.")
        print("=" * 70)
    else:
        print("⚠️  No execution ID found (might not have been created)")
else:
    print("⚠️  Cloud uploader not available - telemetry may not have been uploaded")
    print("   Make sure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set")

print()
print("🎉 Demo complete! Check your monitoring platform to see the data.")
