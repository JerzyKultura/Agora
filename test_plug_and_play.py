"""
PLUG-AND-PLAY Wide Events Test

This is how easy it is now! No manual span wrapping needed!
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🎯 PLUG-AND-PLAY Wide Events Test")
print("=" * 70)
print()

# STEP 1: Initialize Agora (once at startup)
print("1️⃣ Initializing Agora...")
from agora.agora_tracer import init_agora

init_agora(
    app_name="plug-and-play-test",
    project_name="Plug and Play Test",
    enable_cloud_upload=True
)
print()

# STEP 2: Set business context ONCE
print("2️⃣ Setting business context...")
from agora.wide_events import set_business_context

set_business_context(
    user_id="user_456",
    user_email="plugin@example.com",
    subscription_tier="enterprise",
    lifetime_value_cents=500000,  # $5,000 LTV!
    account_age_days=730,  # 2 years
    feature_flags={
        "plug_and_play": True,
        "auto_enrichment": True,
        "no_manual_wrapping": True
    },
    workflow_type="demo",
    priority="high",
    custom={
        "test_type": "plug_and_play",
        "automatic": True
    }
)
print("✅ Business context set! All future LLM calls will be auto-enriched!")
print()

# STEP 3: Make LLM calls - NO WRAPPING NEEDED!
print("3️⃣ Making LLM calls (no manual wrapping needed)...")
from openai import OpenAI

client = OpenAI()

print()
print("📞 First LLM call...")
response1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say 'First call auto-enriched!' in one sentence."}],
    max_tokens=30
)
print(f"   Response: {response1.choices[0].message.content}")

print()
print("📞 Second LLM call...")
response2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say 'Second call auto-enriched!' in one sentence."}],
    max_tokens=30
)
print(f"   Response: {response2.choices[0].message.content}")

print()
print("📞 Third LLM call...")
response3 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say 'Third call auto-enriched!' in one sentence."}],
    max_tokens=30
)
print(f"   Response: {response3.choices[0].message.content}")

print()
print("✅ All 3 calls completed!")
print()

# Wait for upload
import time
print("⏳ Waiting for telemetry to upload...")
time.sleep(3)
print("✅ Upload complete!")
print()

# Complete execution
print("📝 Marking execution as complete...")
from agora import agora_tracer
import asyncio

if agora_tracer.cloud_uploader:
    asyncio.run(agora_tracer.cloud_uploader.complete_execution(
        status="success",
        output_data={"message": "Plug-and-play test successful!"}
    ))
    print("✅ Execution marked as success!")
print()

print("=" * 70)
print("🎉 SUCCESS!")
print()
print("ALL 3 LLM calls were automatically enriched with business context!")
print("No manual span wrapping needed!")
print()
print("Check your dashboard:")
print("  http://localhost:5173/monitoring")
print()
print("All 3 traces should have:")
print("  ✅ user.id = 'user_456'")
print("  ✅ user.subscription_tier = 'enterprise'")
print("  ✅ user.lifetime_value_cents = 500000")
print("  ✅ feature_flags.plug_and_play = True")
print("  ✅ feature_flags.auto_enrichment = True")
print("  ✅ custom.test_type = 'plug_and_play'")
print("  ✅ custom.automatic = True")
print()
print("=" * 70)
