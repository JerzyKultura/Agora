#!/usr/bin/env python3
"""
Quick test to verify chat messages are being captured in telemetry
"""

import os
from dotenv import load_dotenv
load_dotenv()

# Initialize Traceloop (auto-instruments OpenAI)
from traceloop.sdk import Traceloop
Traceloop.init(
    app_name="chat-test",
    disable_batch=True
)

# Initialize Agora
from agora.agora_tracer import init_agora
init_agora(
    app_name="chat-test",
    project_name="Chat Test",
    enable_cloud_upload=True
)

# Make a simple chat call
from openai import OpenAI
client = OpenAI()

print("🤖 Sending chat message to OpenAI...")
print("=" * 60)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2? Answer in one sentence."}
    ],
    temperature=0.7,
    max_tokens=50
)

print(f"✅ Response: {response.choices[0].message.content}")
print("=" * 60)
print()
print("📊 Check your telemetry:")
print("   - Traceloop: https://app.traceloop.com")
print("   - Agora: http://localhost:5173/monitoring")
print()
print("💡 You should see:")
print("   1. A trace with 1 LLM call")
print("   2. Click the trace to see the span list")
print("   3. Click the 'openai.chat' span")
print("   4. The Prompt tab should show the messages")
print("   5. The Completions tab should show the response")
