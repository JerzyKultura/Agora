#!/usr/bin/env python3
"""
Agora Chatbot Demo: Zilliz + Mem0
Traces a memory-augmented chatbot pipeline in real-time.
"""

import asyncio
import random
import os
from agora.agora_tracer import init_agora, agora_node, TracedAsyncFlow

# --- Setup ---
init_agora(
    app_name="agora-chatbot",
    project_name="AI Chatbot",
    export_to_console=False
)

# --- Mock Advanced Tools ---
class MockZilliz:
    async def search(self, query):
        await asyncio.sleep(0.8)  # Simulate network latency
        return [
            {"id": 1, "text": "Agora is a self-hosted telemetry platform.", "score": 0.98},
            {"id": 2, "text": "It supports real-time Python workflow tracing.", "score": 0.92}
        ]

class MockMem0:
    async def get_history(self, user_id):
        await asyncio.sleep(0.4)
        return ["User previously asked about self-hosting.", "User prefers light mode."]

zilliz = MockZilliz()
memory = MockMem0()

# --- Agora Nodes ---

@agora_node(name="IngestInput")
async def ingest_input(shared):
    print(f"👤 User: {shared['user_query']}")
    shared["user_id"] = "user_123"
    return "memory"

@agora_node(name="RetrieveMemory")
async def retrieve_memory(shared):
    print("🧠 Fetching user context from Mem0...")
    history = await memory.get_history(shared["user_id"])
    shared["chat_history"] = history
    return "search"

@agora_node(name="VectorSearch")
async def vector_search(shared):
    print("🔍 Searching Zilliz Vector DB for relevant docs...")
    docs = await zilliz.search(shared["user_query"])
    shared["retrieved_docs"] = docs
    return "generate"

@agora_node(name="GenerateResponse")
async def generate_response(shared):
    print("🤖 Synthesizing answer...")
    await asyncio.sleep(1.2) # Simulate LLM generation
    
    # Simple logic
    context = "\n".join([d["text"] for d in shared["retrieved_docs"]])
    response = f"Based on your interest in {shared['chat_history'][-1]}, Agora is great because {context}"
    
    shared["ai_response"] = response
    print(f"✨ AI: {response}")
    return None

async def run_chatbot():
    # Define Flow
    flow = TracedAsyncFlow("ChatbotPipeline")
    flow.start(ingest_input)

    # Connections
    ingest_input - "memory" >> retrieve_memory
    retrieve_memory - "search" >> vector_search
    vector_search - "generate" >> generate_response

    # Run
    print("\n" + "="*60)
    print("🚀 Running AI Chatbot Pipeline (Tracing via Agora)")
    print("="*60 + "\n")

    shared = {"user_query": "How does Agora work?"}
    await flow.run_async(shared)

    print("\n" + "="*60)
    print("✓ Chatbot finished! Check your Agora dashboard for real-time spans.")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_chatbot())
