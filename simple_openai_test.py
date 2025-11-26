#!/usr/bin/env python3
"""
Simple OpenAI API Test
======================

Minimal script to test if your OpenAI API key works.
Copy this to Colab or run locally.

Usage in Colab:
1. Replace "your-openai-key-here" with your actual key
2. Run the cell
3. Should see a response in ~2-3 seconds

Usage locally:
1. export OPENAI_API_KEY="sk-..."
2. python simple_openai_test.py
"""

# For Colab: Uncomment and run this first
# !pip install openai

import os
from openai import OpenAI

# =============================================================================
# PASTE YOUR OPENAI API KEY HERE
# =============================================================================

OPENAI_API_KEY = "sk-..."  # <- Replace with your key

# Or use environment variable
# OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# =============================================================================
# TEST THE API
# =============================================================================

def test_openai():
    """Test if OpenAI API key works"""

    if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-...":
        print("❌ ERROR: Please set your OPENAI_API_KEY")
        print("Get a key from: https://platform.openai.com/api-keys")
        return False

    print("Testing OpenAI API...")
    print(f"Key: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:]}")
    print()

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        print("Sending test message to GPT-4o-mini...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello! API test successful!' and nothing else."}
            ],
            max_tokens=50
        )

        result = response.choices[0].message.content
        print(f"\n✅ SUCCESS!")
        print(f"Response: {result}")
        print()
        print(f"Model: {response.model}")
        print(f"Tokens used: {response.usage.total_tokens}")
        print(f"Cost: ~${response.usage.total_tokens * 0.00000015:.6f}")
        print()
        print("✓ Your OpenAI API key is working!")
        return True

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ERROR: {error_msg}\n")

        if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
            print("Problem: Invalid API key")
            print("Solution:")
            print("  1. Go to: https://platform.openai.com/api-keys")
            print("  2. Create a new API key")
            print("  3. Copy the key (starts with 'sk-')")
            print("  4. Paste it in this script where it says OPENAI_API_KEY")

        elif "quota" in error_msg.lower() or "insufficient" in error_msg.lower():
            print("Problem: Insufficient credits")
            print("Solution:")
            print("  1. Go to: https://platform.openai.com/account/billing")
            print("  2. Add credits to your account")
            print("  3. Try again")

        elif "rate_limit" in error_msg.lower():
            print("Problem: Rate limit exceeded")
            print("Solution:")
            print("  1. Wait a few seconds")
            print("  2. Try again")

        else:
            print("Solution:")
            print("  1. Check your internet connection")
            print("  2. Check OpenAI status: https://status.openai.com")
            print("  3. Verify your API key is correct")

        return False

if __name__ == "__main__":
    print("=" * 60)
    print("OPENAI API TEST")
    print("=" * 60)
    print()

    success = test_openai()

    print()
    print("=" * 60)
    if success:
        print("NEXT STEPS")
        print("=" * 60)
        print()
        print("Now that your OpenAI key works, try:")
        print("  1. colab_demo.py - Full chatbot with Agora tracing")
        print("  2. demo_workflow.py - Workflow with loop example")
        print()
        print("To add Agora Cloud telemetry:")
        print("  1. Deploy your platform")
        print("  2. Go to Settings → Generate API Key")
        print("  3. Set: os.environ['AGORA_API_KEY'] = 'agora_...'")
