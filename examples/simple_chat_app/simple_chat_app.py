# ============================================================================
# AGORA CHAT WITH OPENTELEMETRY - MINIMAL VERSION
# ============================================================================

!pip install --force-reinstall git+https://github.com/JerzyKultura/Agora.git
!pip install openai opentelemetry-instrumentation-openai

import os
from openai import OpenAI
from agora.telemetry import AuditLogger, AuditedNode, AuditedFlow

# Auto-instrument OpenAI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
OpenAIInstrumentor().instrument()

# ============================================================================
# LLM + CHAT NODES
# ============================================================================

def call_llm(messages):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "paste-your-openai-key-here"))
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, temperature=0.7, max_tokens=500
    )
    return response.choices[0].message.content

class ChatInput(AuditedNode):
    def prep(self, shared):
        if "messages" not in shared:
            shared["messages"] = []
            print("Chat ready. Type 'exit' to quit.")
        return shared["messages"]

    def exec(self, messages):
        user_input = input("\nYou: ").strip()
        return user_input if user_input.lower() != 'exit' else None

    def post(self, shared, prep_res, exec_res):
        if exec_res is None:
            return "exit"
        shared["messages"].append({"role": "user", "content": exec_res})
        return "respond"

class ChatResponse(AuditedNode):
    def prep(self, shared):
        return shared["messages"]

    def exec(self, messages):
        response = call_llm(messages)  # Auto-instrumented
        return response

    def post(self, shared, prep_res, exec_res):
        print(f"\nBot: {exec_res}")
        shared["messages"].append({"role": "assistant", "content": exec_res})
        return "input"

class ChatExit(AuditedNode):
    def exec(self, prep_res):
        print("Goodbye!")
        return None

# ============================================================================
# RUN CHAT
# ============================================================================

def run_chat():
    logger = AuditLogger("chat")

    # Create nodes
    chat_input = ChatInput("Input", logger)
    chat_response = ChatResponse("Response", logger)
    chat_exit = ChatExit("Exit", logger)

    # Build flow
    flow = AuditedFlow("Chat", logger)
    flow.start(chat_input)
    chat_input - "respond" >> chat_response
    chat_input - "exit" >> chat_exit
    chat_response - "input" >> chat_input

    # Run
    shared = {}
    flow.run(shared)

    # Show results
    print(f"\nAudit: {logger.get_summary()}")
    logger.save_json("chat_audit.json")

# Set your API key and run
# os.environ["OPENAI_API_KEY"] = "your-key-here"
# run_chat()

print("Set API key: os.environ['OPENAI_API_KEY'] = 'your-key'")
print("Then run: run_chat()")

run_chat()
