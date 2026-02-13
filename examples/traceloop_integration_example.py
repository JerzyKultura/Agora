#!/usr/bin/env python3
"""
Example: Traceloop Integration with Agora

This script demonstrates how to use Traceloop/OpenLLMetry to automatically
send OpenTelemetry traces to the Agora platform.

Requirements:
    pip install traceloop-sdk openai python-dotenv

Environment Variables:
    AGORA_API_KEY: Your Agora API key (agora_xxx)
    AGORA_API_ENDPOINT: Your Agora backend URL (default: http://localhost:8000)
    OPENAI_API_KEY: Your OpenAI API key
"""

import os
from dotenv import load_dotenv
from traceloop.sdk import Traceloop
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
AGORA_API_KEY = os.getenv("AGORA_API_KEY", "agora_kZm1BBglxdHyEyaz1NmpxowSLbYvZWyK")
AGORA_API_ENDPOINT = os.getenv("AGORA_API_ENDPOINT", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY not set in environment")
    exit(1)

print("🚀 Initializing Traceloop with Agora backend")
print(f"   Endpoint: {AGORA_API_ENDPOINT}/telemetry/traces")
print(f"   API Key: {AGORA_API_KEY[:20]}...")
print()

# Initialize Traceloop to send traces to Agora
Traceloop.init(
    app_name="agora-traceloop-example",
    api_endpoint=f"{AGORA_API_ENDPOINT}/telemetry/traces",
    headers={
        "Authorization": f"Bearer {AGORA_API_KEY}"
    },
    # Optional: Add custom resource attributes
    resource_attributes={
        "service.name": "agora-example",
        "service.version": "1.0.0",
        "deployment.environment": "development"
    }
)

print("✅ Traceloop initialized")
print()

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

print("🤖 Making OpenAI API call...")
print("   This will automatically send telemetry to Agora")
print()

# Make an OpenAI call - telemetry is automatic!
try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain quantum computing in one sentence."}
        ],
        max_tokens=100
    )
    
    print("✅ OpenAI Response:")
    print(f"   {response.choices[0].message.content}")
    print()
    
    print("📊 Telemetry Info:")
    print(f"   Model: {response.model}")
    print(f"   Prompt Tokens: {response.usage.prompt_tokens}")
    print(f"   Completion Tokens: {response.usage.completion_tokens}")
    print(f"   Total Tokens: {response.usage.total_tokens}")
    print()
    
    print("🎉 Success!")
    print("   Check your Agora dashboard to see the telemetry data")
    print(f"   Dashboard: {AGORA_API_ENDPOINT.replace('8000', '5173')}/monitoring")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
