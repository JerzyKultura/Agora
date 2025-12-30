"""
🎯 TRACELOOP-ONLY CHATBOT FOR GOOGLE COLAB
============================================

QUICK START:
1. Copy this entire code into a Google Colab cell
2. Replace the API keys below (lines 22-23)
3. Run the cell
4. View telemetry at: https://app.traceloop.com

This is a minimal example to see Traceloop's telemetry in action!
"""

# ============================================================================
# STEP 1: Install packages
# ============================================================================

get_ipython().system('pip install -q traceloop-sdk openai')

# ============================================================================
# STEP 2: Set your API keys
# ============================================================================

OPENAI_API_KEY = "sk-..."  # ← Get from https://platform.openai.com/api-keys
TRACELOOP_API_KEY = "tl_6894c89d3a0343afab2828f7cf371a25"  # ← Your Traceloop key

# ============================================================================
# STEP 3: Initialize Traceloop
# ============================================================================

import os
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

from traceloop.sdk import Traceloop
from openai import OpenAI

print("🔧 Initializing Traceloop...")
Traceloop.init(
    app_name="colab-chatbot",
    disable_batch=True,  # Real-time telemetry
    api_key=TRACELOOP_API_KEY
)
print("✅ Traceloop ready!")
print("📊 Dashboard: https://app.traceloop.com")
print()

# ============================================================================
# STEP 4: Create chatbot
# ============================================================================

client = OpenAI()

def ask(question: str) -> str:
    """Ask a question and get an answer (automatically traced!)"""
    print(f"💭 Question: {question}")
    print("🤖 Thinking...")

    # This OpenAI call is automatically traced by Traceloop!
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": question}
        ],
        temperature=0.7
    )

    answer = response.choices[0].message.content
    usage = response.usage

    print(f"💬 Answer: {answer}")
    print()
    print(f"📊 Stats:")
    print(f"   • Tokens: {usage.total_tokens} ({usage.prompt_tokens} prompt + {usage.completion_tokens} completion)")
    print(f"   • Cost: ~${usage.total_tokens * 0.00000015:.6f}")
    print(f"   • Model: gpt-4o-mini")
    print()

    return answer

# ============================================================================
# STEP 5: Run demo queries
# ============================================================================

print("=" * 70)
print("🚀 RUNNING DEMO")
print("=" * 70)
print()
print("Asking 3 questions...")
print("Watch them appear at: https://app.traceloop.com")
print()

# Question 1
print("━" * 70)
print("QUESTION 1/3")
print("━" * 70)
ask("What is machine learning?")

import time
time.sleep(1)

# Question 2
print("━" * 70)
print("QUESTION 2/3")
print("━" * 70)
ask("Explain neural networks in simple terms")

time.sleep(1)

# Question 3
print("━" * 70)
print("QUESTION 3/3")
print("━" * 70)
ask("What's the difference between AI and ML?")

# ============================================================================
# DONE!
# ============================================================================

print("=" * 70)
print("✅ DEMO COMPLETE!")
print("=" * 70)
print()
print("📊 View your telemetry at: https://app.traceloop.com")
print()
print("You should see:")
print("   ✓ 3 OpenAI completion spans")
print("   ✓ Full prompts and responses")
print("   ✓ Token usage (prompt + completion)")
print("   ✓ Model name (gpt-4o-mini)")
print("   ✓ Temperature (0.7)")
print("   ✓ Latency timings")
print()
print("Compare this with your Agora Live Telemetry!")
print()

# ============================================================================
# OPTIONAL: Interactive mode
# ============================================================================

print("Want to ask your own questions? Run this:")
print()
print("while True:")
print("    q = input('Ask: ')")
print("    if q.lower() == 'exit': break")
print("    ask(q)")
