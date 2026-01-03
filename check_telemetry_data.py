#!/usr/bin/env python3
"""
Check what telemetry data is actually in the database
"""

import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

supabase_url = os.getenv("VITE_SUPABASE_URL")
supabase_key = os.getenv("VITE_SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    print("❌ Missing Supabase credentials in .env file")
    print("   Need: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY")
    exit(1)

print(f"🔗 Connecting to Supabase...")
print(f"   URL: {supabase_url}")
supabase = create_client(supabase_url, supabase_key)

# Get recent telemetry spans
print("\n📊 Fetching recent telemetry spans...")
result = supabase.table('telemetry_spans').select('*').order('created_at', desc=True).limit(5).execute()

if not result.data:
    print("❌ No telemetry spans found in database!")
    print("   Run a demo script first: python test_chat_messages.py")
else:
    print(f"✅ Found {len(result.data)} recent spans\n")

    for i, span in enumerate(result.data, 1):
        print(f"{'='*60}")
        print(f"Span {i}: {span['name']}")
        print(f"{'='*60}")
        print(f"Trace ID: {span['trace_id'][:16]}...")
        print(f"Span ID:  {span['span_id'][:16]}...")
        print(f"Status:   {span['status']}")
        print(f"Duration: {span['duration_ms']}ms" if span['duration_ms'] else "Duration: N/A")

        attrs = span.get('attributes', {})

        # Check for LLM attributes
        has_llm = any(key.startswith('gen_ai.') or key.startswith('llm.') for key in attrs.keys())

        if has_llm:
            print(f"\n🤖 LLM Attributes:")
            print(f"   Model:    {attrs.get('gen_ai.request.model', 'N/A')}")
            print(f"   Provider: {attrs.get('gen_ai.system', 'N/A')}")
            print(f"   Tokens:   {attrs.get('gen_ai.usage.input_tokens', 0)} in + {attrs.get('gen_ai.usage.output_tokens', 0)} out")

            # Check for prompts
            prompt_count = 0
            while f'gen_ai.prompt.{prompt_count}.content' in attrs:
                prompt_count += 1

            completion_count = 0
            while f'gen_ai.completion.{completion_count}.content' in attrs:
                completion_count += 1

            print(f"\n📝 Messages:")
            print(f"   Prompts:     {prompt_count} message(s)")
            print(f"   Completions: {completion_count} message(s)")

            if prompt_count > 0:
                print(f"\n   Prompt 0 (first 100 chars):")
                content = attrs.get('gen_ai.prompt.0.content', '')
                print(f"   {content[:100]}...")
            else:
                print(f"\n   ⚠️  NO PROMPTS FOUND - This is the issue!")

            if completion_count > 0:
                print(f"\n   Completion 0 (first 100 chars):")
                content = attrs.get('gen_ai.completion.0.content', '')
                print(f"   {content[:100]}...")
            else:
                print(f"\n   ⚠️  NO COMPLETIONS FOUND")
        else:
            print(f"\n   (Not an LLM span)")

        print()

print("\n" + "="*60)
print("💡 To see full attributes, check: /monitoring in your web UI")
print("="*60)
