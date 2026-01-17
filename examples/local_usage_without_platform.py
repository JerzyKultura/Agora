"""
=============================================================================
USING AGORA LOCALLY - NO PLATFORM NEEDED
=============================================================================

This guide shows you 5 different ways to use Agora locally without the
monitoring platform. Choose based on your needs:

1. Pure Agora (no telemetry at all)
2. Console logging only (see traces in terminal)
3. File logging (save traces to JSON file)
4. AuditLogger only (simple JSON audit trails)
5. Full telemetry with local-only OpenTelemetry

=============================================================================
"""

import os
from openai import OpenAI

# =============================================================================
# OPTION 1: PURE AGORA - NO TELEMETRY AT ALL
# =============================================================================
# Use basic Node/Flow without any tracing or logging
# Perfect for: Simple workflows, development, testing

def option1_pure_agora():
    """Use Agora's core workflow engine without any telemetry"""

    from agora import AsyncNode, AsyncFlow

    class FetchData(AsyncNode):
        async def exec_async(self, prep_res):
            # Your logic here
            return {"data": "fetched"}

    class ProcessData(AsyncNode):
        async def exec_async(self, prep_res):
            data = prep_res
            return f"Processed: {data}"

    # Build workflow
    fetch = FetchData()
    process = ProcessData()

    flow = AsyncFlow()
    flow.start(fetch) >> process

    # Run
    import asyncio
    shared = {}
    result = asyncio.run(flow.run(shared))
    print(f"Result: {result}")

    print("\n✅ Pure Agora - No telemetry, just workflows")


# =============================================================================
# OPTION 2: CONSOLE LOGGING - SEE TRACES IN TERMINAL
# =============================================================================
# OpenTelemetry traces printed to console
# Perfect for: Development, debugging, seeing what's happening

def option2_console_logging():
    """Use Agora with console-only telemetry (no cloud upload)"""

    from agora.agora_tracer import init_agora
    from openai import OpenAI

    # Initialize with console export ONLY
    init_agora(
        app_name="local-dev",
        export_to_console=True,       # Print spans to console
        enable_cloud_upload=False     # NO cloud upload
    )

    # Now use OpenAI - traces print to console
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=50
    )

    print(f"Response: {response.choices[0].message.content}")
    print("\n✅ Console logging - Traces printed to terminal")


# =============================================================================
# OPTION 3: FILE LOGGING - SAVE TRACES TO JSON
# =============================================================================
# OpenTelemetry traces saved to a local file
# Perfect for: Keeping a record, analyzing later, CI/CD

def option3_file_logging():
    """Use Agora with file-based telemetry (no cloud upload)"""

    from agora.agora_tracer import init_agora
    from openai import OpenAI

    # Initialize with file export ONLY
    init_agora(
        app_name="local-file",
        export_to_file="telemetry.jsonl",  # Write to file
        enable_cloud_upload=False           # NO cloud upload
    )

    # Use OpenAI - traces saved to telemetry.jsonl
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=50
    )

    print(f"Response: {response.choices[0].message.content}")
    print("\n✅ File logging - Traces saved to telemetry.jsonl")
    print("   You can read it with: cat telemetry.jsonl | jq")


# =============================================================================
# OPTION 4: AUDIT LOGGER ONLY - SIMPLE JSON AUDIT TRAILS
# =============================================================================
# Use Agora's built-in AuditLogger without OpenTelemetry
# Perfect for: Simple audit trails, debugging workflows

def option4_audit_logger():
    """Use Agora's AuditLogger for simple JSON audit trails"""

    from agora.telemetry import AuditLogger, AuditedNode, AuditedFlow
    from openai import OpenAI

    # Create audit logger (no OpenTelemetry needed!)
    logger = AuditLogger("my-workflow")

    class ChatNode(AuditedNode):
        def __init__(self, name, audit_logger):
            super().__init__(name, audit_logger)
            self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

        def exec(self, prep_res):
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=50
            )
            return response.choices[0].message.content

    # Create node with audit logger
    chat = ChatNode("Chat", logger)

    # Create audited flow
    flow = AuditedFlow("MyFlow", logger)
    flow.start(chat)

    # Run
    result = flow.run({})
    print(f"Result: {result}")

    # Get audit trail
    print("\n📊 Audit Trail:")
    print(logger.get_summary())

    # Save to JSON file
    logger.save_json("audit_trail.json")
    print("✅ Audit logger - Saved to audit_trail.json")


# =============================================================================
# OPTION 5: LOCAL OPENTELEMETRY - FULL TRACES, NO CLOUD
# =============================================================================
# Full OpenTelemetry instrumentation with local-only export
# Perfect for: Full observability without external dependencies

def option5_local_opentelemetry():
    """Use full OpenTelemetry with local export (no Agora platform)"""

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor
    from openai import OpenAI

    # Setup OpenTelemetry with console exporter
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        SimpleSpanProcessor(ConsoleSpanExporter())
    )

    # Auto-instrument OpenAI
    OpenAIInstrumentor().instrument()

    # Now all OpenAI calls are traced
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=50
    )

    print(f"Response: {response.choices[0].message.content}")
    print("\n✅ Local OpenTelemetry - Full traces, no cloud")


# =============================================================================
# BONUS: COMBINE MULTIPLE OPTIONS
# =============================================================================

def bonus_combined():
    """Combine console + file logging for best of both worlds"""

    from agora.agora_tracer import init_agora
    from openai import OpenAI

    # Initialize with BOTH console AND file export
    init_agora(
        app_name="local-combined",
        export_to_console=True,           # Print to terminal
        export_to_file="traces.jsonl",    # AND save to file
        enable_cloud_upload=False         # NO cloud upload
    )

    # Use OpenAI
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=50
    )

    print(f"Response: {response.choices[0].message.content}")
    print("\n✅ Combined - Traces in console AND file")


# =============================================================================
# COMPARISON TABLE
# =============================================================================

"""
┌─────────────────────┬────────────┬──────────┬────────────┬──────────────┐
│ Method              │ Telemetry  │ Console  │ File       │ Dependencies │
├─────────────────────┼────────────┼──────────┼────────────┼──────────────┤
│ 1. Pure Agora       │ None       │ No       │ No         │ Just agora   │
│ 2. Console Logging  │ OTel spans │ Yes      │ No         │ + traceloop  │
│ 3. File Logging     │ OTel spans │ No       │ Yes        │ + traceloop  │
│ 4. AuditLogger      │ JSON audit │ Yes      │ Optional   │ Just agora   │
│ 5. Local OTel       │ OTel spans │ Yes      │ No         │ + otel-sdk   │
│ Bonus: Combined     │ OTel spans │ Yes      │ Yes        │ + traceloop  │
└─────────────────────┴────────────┴──────────┴────────────┴──────────────┘

RECOMMENDATION:
- Development: Option 2 (Console) or Option 4 (AuditLogger)
- Production: Option 3 (File) or send to your own OTel collector
- Testing: Option 1 (Pure) - fastest, no overhead
- Debugging: Bonus (Combined) - see everything everywhere
"""

# =============================================================================
# SIMPLE WORKFLOW EXAMPLE (NO PLATFORM)
# =============================================================================

def simple_workflow_example():
    """A complete workflow example with local-only telemetry"""

    from agora import AsyncNode, AsyncFlow
    from agora.agora_tracer import init_agora
    from openai import OpenAI
    import asyncio

    # Initialize with file logging (no cloud)
    init_agora(
        app_name="simple-workflow",
        export_to_file="workflow.jsonl",
        enable_cloud_upload=False
    )

    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    class GenerateIdea(AsyncNode):
        async def exec_async(self, prep_res):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Give me a startup idea"}],
                max_tokens=100
            )
            return response.choices[0].message.content

    class EvaluateIdea(AsyncNode):
        async def exec_async(self, prep_res):
            idea = prep_res
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": f"Rate this startup idea: {idea}"}
                ],
                max_tokens=100
            )
            return response.choices[0].message.content

    # Build workflow
    generate = GenerateIdea()
    evaluate = EvaluateIdea()

    flow = AsyncFlow()
    flow.start(generate) >> evaluate

    # Run
    result = asyncio.run(flow.run({}))
    print(f"\nResult: {result}")
    print("\n✅ Workflow complete - traces saved to workflow.jsonl")


# =============================================================================
# RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("AGORA LOCAL USAGE - NO PLATFORM NEEDED")
    print("=" * 80)
    print()

    print("Uncomment the example you want to run:\n")

    # Uncomment one to try:
    # option1_pure_agora()
    # option2_console_logging()
    # option3_file_logging()
    # option4_audit_logger()
    # option5_local_opentelemetry()
    # bonus_combined()
    # simple_workflow_example()

    print("Examples:")
    print("  option1_pure_agora()           - No telemetry")
    print("  option2_console_logging()      - Print traces to console")
    print("  option3_file_logging()         - Save traces to file")
    print("  option4_audit_logger()         - Simple JSON audit trail")
    print("  option5_local_opentelemetry()  - Full OTel, local only")
    print("  bonus_combined()               - Console + file")
    print("  simple_workflow_example()      - Complete workflow")
