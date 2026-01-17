"""
MINIMAL AGORA EXAMPLE - NO PLATFORM NEEDED
Just copy-paste and run!
"""

import os
from openai import OpenAI

# =============================================================================
# OPTION A: Simplest - Console logging only
# =============================================================================

def run_with_console():
    """See traces in your terminal"""

    from agora.agora_tracer import init_agora

    # Initialize Agora with console output ONLY (no cloud upload)
    init_agora(
        app_name="my-local-app",
        export_to_console=True,       # ✅ Print spans to console
        enable_cloud_upload=False     # ❌ No cloud upload
    )

    # Use OpenAI - automatically traced!
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    print("Calling OpenAI...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Explain Agora in one sentence"}
        ],
        max_tokens=50
    )

    print(f"\nResponse: {response.choices[0].message.content}\n")
    print("✅ Done! Check the console output above for telemetry spans.")


# =============================================================================
# OPTION B: File logging - Save traces to file
# =============================================================================

def run_with_file():
    """Save traces to a JSON file"""

    from agora.agora_tracer import init_agora

    # Initialize Agora with file output ONLY
    init_agora(
        app_name="my-local-app",
        export_to_file="traces.jsonl",  # ✅ Save to file
        enable_cloud_upload=False        # ❌ No cloud upload
    )

    # Use OpenAI
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    print("Calling OpenAI...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Explain Agora in one sentence"}
        ],
        max_tokens=50
    )

    print(f"\nResponse: {response.choices[0].message.content}\n")
    print("✅ Done! Traces saved to traces.jsonl")
    print("   View with: cat traces.jsonl | jq")


# =============================================================================
# OPTION C: Pure Agora - No telemetry at all
# =============================================================================

def run_pure_agora():
    """Use Agora workflows without any telemetry"""

    from agora import AsyncNode, AsyncFlow
    import asyncio

    class MyNode(AsyncNode):
        async def exec_async(self, prep_res):
            client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Explain Agora in one sentence"}],
                max_tokens=50
            )
            return response.choices[0].message.content

    # Build workflow
    node = MyNode()
    flow = AsyncFlow()
    flow.start(node)

    # Run
    print("Running workflow...")
    result = asyncio.run(flow.run({}))
    print(f"\nResult: {result}\n")
    print("✅ Done! Pure workflow, no telemetry.")


# =============================================================================
# RUN IT!
# =============================================================================

if __name__ == "__main__":
    import sys

    # Check if OpenAI API key is set
    if not os.environ.get('OPENAI_API_KEY'):
        print("❌ Please set your OpenAI API key first:")
        print("   os.environ['OPENAI_API_KEY'] = 'sk-...'")
        print("\nOr run from command line:")
        print("   OPENAI_API_KEY=sk-... python minimal_local_example.py console")
        sys.exit(1)

    # Check command line argument
    mode = sys.argv[1] if len(sys.argv) > 1 else "console"

    print("=" * 80)
    print(f"RUNNING AGORA LOCALLY - MODE: {mode.upper()}")
    print("=" * 80)
    print()

    if mode == "console":
        run_with_console()
    elif mode == "file":
        run_with_file()
    elif mode == "pure":
        run_pure_agora()
    else:
        print("Usage: python minimal_local_example.py [console|file|pure]")
        print()
        print("  console - Print traces to terminal")
        print("  file    - Save traces to traces.jsonl")
        print("  pure    - No telemetry at all")
