#!/usr/bin/env python3
"""
Agora Demo with LLM Calls
==========================

This demo shows REAL LLM telemetry with prompts, responses, tokens, and costs
appearing in your Live Telemetry dashboard.

Setup:
1. Set environment variables:
   export OPENAI_API_KEY="sk-..."
   export VITE_SUPABASE_URL="https://your-project.supabase.co"
   export VITE_SUPABASE_ANON_KEY="eyJhbGci..."

2. Run: python demo_with_llm.py

3. Watch http://localhost:5173/live to see LLM calls in real-time!
"""

import asyncio
import os
from openai import OpenAI

from agora.agora_tracer import (
    TracedAsyncFlow,
    init_agora,
    agora_node,
)

# Initialize Agora telemetry (Traceloop automatically instruments OpenAI!)
init_agora(
    app_name="talking-chatbot",
    project_name="Production Chatbot",
    export_to_console=False,
    enable_cloud_upload=True,
    capture_io=True  # Capture input/output in spans
)

# Initialize OpenAI client (NO manual instrumentation needed!)
# Traceloop SDK already instruments it automatically
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@agora_node(name="MemoryRetrieval")
async def memory_retrieval(shared):
    """Simulate retrieving user memory/context"""
    print("🧠 Checking Mem0 history for user_456...")

    # Simulate memory lookup
    await asyncio.sleep(0.5)

    shared["user_memory"] = "User likes efficient telemetry."
    shared["user_id"] = "user_456"

    return "search"


@agora_node(name="VectorSearch")
async def vector_search(shared):
    """Simulate vector database search"""
    print("🔍 Searching Vector DB...")

    query = shared.get("user_query", "What is telemetry?")

    # Simulate vector search
    await asyncio.sleep(0.2)

    shared["context"] = "Telemetry is the automatic measurement and transmission of data from remote sources."

    return "synthesize"


@agora_node(name="SynthesizeResponse")
async def synthesize_response(shared):
    """Call LLM to generate response - THIS WILL SHOW IN LIVE TELEMETRY"""
    print("🤖 Synthesizing answer...")

    user_query = shared.get("user_query", "What is telemetry?")
    context = shared.get("context", "")
    user_memory = shared.get("user_memory", "")

    # 🔥 THIS IS THE LLM CALL THAT WILL APPEAR IN LIVE TELEMETRY
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful assistant. User context: {user_memory}"
            },
            {
                "role": "user",
                "content": f"Context: {context}\n\nQuestion: {user_query}"
            }
        ],
        temperature=0.7,
        max_tokens=150
    )

    answer = response.choices[0].message.content
    shared["answer"] = answer

    print(f"\n💬 Answer: {answer}\n")
    print(f"📊 Tokens: {response.usage.total_tokens}")
    print(f"💰 Cost: ~${response.usage.total_tokens * 0.00000015:.6f}\n")

    return "finish"


@agora_node(name="Finish")
async def finish_node(shared):
    """Complete the workflow"""
    print("✅ Done!")
    return None


async def run_chatbot_demo():
    """Run the chatbot workflow with LLM calls"""

    print("=" * 60)
    print("🤖 AGORA CHATBOT DEMO WITH LIVE LLM TELEMETRY")
    print("=" * 60)
    print()
    print("This will make REAL OpenAI API calls.")
    print("Watch http://localhost:5173/live to see:")
    print("  - Prompts sent to OpenAI")
    print("  - Responses from GPT-4o-mini")
    print("  - Token usage & costs")
    print("  - Node execution timeline")
    print()
    print("=" * 60)
    print()

    # Create workflow
    flow = TracedAsyncFlow("TalkingChatbot")
    flow.start(memory_retrieval)

    memory_retrieval - "search" >> vector_search
    vector_search - "synthesize" >> synthesize_response
    synthesize_response - "finish" >> finish_node

    # Test queries
    queries = [
        "What is telemetry?",
        "How does distributed tracing work?",
        "Explain OpenTelemetry in simple terms"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 60}")
        print(f"QUERY {i}/{len(queries)}")
        print(f"{'=' * 60}\n")
        print(f"❓ User asks: {query}\n")

        shared = {"user_query": query}
        await flow.run_async(shared)

        print(f"\n✅ Check http://localhost:5173/live")

        if i < len(queries):
            print("\nWaiting 3 seconds before next query...")
            await asyncio.sleep(3)

    print()
    print("=" * 60)
    print("✓ All queries completed!")
    print("=" * 60)
    print()
    print("🎯 Now check your Live Telemetry dashboard:")
    print("   http://localhost:5173/live")
    print()
    print("You should see:")
    print("  ✓ Purple LLM spans with prompts/responses")
    print("  ✓ Blue Agora node spans")
    print("  ✓ Token counts and costs")
    print("  ✓ Trace IDs linking everything together")
    print()


if __name__ == "__main__":
    # Check for OpenAI key
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not set!")
        print()
        print("Set it with:")
        print('  export OPENAI_API_KEY="sk-..."')
        print()
        exit(1)

    asyncio.run(run_chatbot_demo())