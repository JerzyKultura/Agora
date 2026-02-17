"""
Agora Colab Demo - Production-Ready Example
============================================
A comprehensive example showing best practices for using Agora in Google Colab.

This example demonstrates:
- Proper initialization with telemetry
- Error handling and validation
- Real-world API integration (OpenAI)
- Multi-node workflow with data transformation
- Shared state management
- Async/await patterns
"""

import os
import asyncio
from typing import Dict, Any, List
from agora.agora_tracer import init_agora, agora_node, TracedAsyncFlow

# ============================================================================
# CONFIGURATION
# ============================================================================

# Initialize Agora with telemetry
# Set your API key as an environment variable: AGORA_API_KEY
init_agora(
    app_name="colab-demo",
    project_name="Agora Production Example",
    enable_cloud_upload=True  # Enable telemetry upload to Agora Cloud
)

# ============================================================================
# WORKFLOW NODES
# ============================================================================

@agora_node(name="FetchUserInput")
async def fetch_user_input(shared: Dict[str, Any]) -> str:
    """
    Fetch and validate user input.
    
    In a real application, this might fetch from a database or API.
    For demo purposes, we'll use a predefined prompt.
    """
    user_prompt = shared.get("user_prompt", "Explain quantum computing in simple terms")
    
    # Validate input
    if not user_prompt or len(user_prompt.strip()) == 0:
        raise ValueError("User prompt cannot be empty")
    
    # Store in shared state
    shared["validated_prompt"] = user_prompt.strip()
    shared["prompt_length"] = len(user_prompt)
    
    print(f"✓ Fetched user input: '{user_prompt[:50]}...'")
    return "process"


@agora_node(name="EnrichPrompt")
async def enrich_prompt(shared: Dict[str, Any]) -> str:
    """
    Enrich the user prompt with context and instructions.
    
    This demonstrates data transformation between nodes.
    """
    base_prompt = shared["validated_prompt"]
    
    # Add context and formatting instructions
    enriched_prompt = f"""You are a helpful AI assistant. Please provide a clear, 
concise answer to the following question:

Question: {base_prompt}

Requirements:
- Keep the response under 200 words
- Use simple language
- Include a practical example if relevant
"""
    
    shared["enriched_prompt"] = enriched_prompt
    print(f"✓ Enriched prompt with context")
    return "generate"


@agora_node(name="GenerateResponse")
async def generate_response(shared: Dict[str, Any]) -> str:
    """
    Generate AI response using OpenAI API.
    
    This demonstrates external API integration with error handling.
    """
    enriched_prompt = shared["enriched_prompt"]
    
    # Check if OpenAI API key is available
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        # Fallback to mock response for demo purposes
        print("⚠ OpenAI API key not found, using mock response")
        mock_response = f"""Quantum computing is a revolutionary approach to computation 
that uses quantum mechanical phenomena like superposition and entanglement. Unlike 
classical computers that use bits (0 or 1), quantum computers use quantum bits or 
'qubits' that can exist in multiple states simultaneously.

Example: Imagine flipping a coin. A classical bit is like a coin that's either heads 
or tails. A qubit is like a spinning coin that's both heads AND tails until you 
observe it. This allows quantum computers to process many possibilities at once, 
making them potentially much faster for certain problems like cryptography and 
drug discovery."""
        
        shared["ai_response"] = mock_response
        shared["response_source"] = "mock"
    else:
        # Real OpenAI API call
        try:
            # Import OpenAI (install with: pip install openai)
            from openai import OpenAI
            
            client = OpenAI(api_key=openai_api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": enriched_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            shared["ai_response"] = ai_response
            shared["response_source"] = "openai"
            shared["tokens_used"] = response.usage.total_tokens
            
            print(f"✓ Generated response using OpenAI ({response.usage.total_tokens} tokens)")
            
        except Exception as e:
            print(f"⚠ OpenAI API error: {e}, using mock response")
            shared["ai_response"] = "Error generating response. Please check your API key."
            shared["response_source"] = "error"
    
    return "format"


@agora_node(name="FormatOutput")
async def format_output(shared: Dict[str, Any]) -> str:
    """
    Format the final output with metadata.
    
    This demonstrates post-processing and result preparation.
    """
    ai_response = shared["ai_response"]
    response_source = shared.get("response_source", "unknown")
    
    # Create formatted output
    formatted_output = {
        "question": shared["validated_prompt"],
        "answer": ai_response,
        "metadata": {
            "source": response_source,
            "prompt_length": shared["prompt_length"],
            "tokens_used": shared.get("tokens_used", "N/A")
        }
    }
    
    shared["final_output"] = formatted_output
    print(f"✓ Formatted final output")
    return "complete"


# ============================================================================
# WORKFLOW DEFINITION
# ============================================================================

def create_workflow() -> TracedAsyncFlow:
    """
    Create and configure the Agora workflow.
    
    This defines the flow of execution between nodes.
    """
    flow = TracedAsyncFlow("AI-Assistant-Pipeline")
    
    # Define the workflow entry point
    flow.start(fetch_user_input)
    
    # Define the workflow graph
    fetch_user_input - "process" >> enrich_prompt
    enrich_prompt - "generate" >> generate_response
    generate_response - "format" >> format_output
    
    return flow


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """
    Main execution function.
    
    This demonstrates how to run the workflow and handle results.
    """
    print("=" * 60)
    print("Agora Production Example - AI Assistant Pipeline")
    print("=" * 60)
    
    # Create workflow
    flow = create_workflow()
    
    # Prepare input data
    initial_input = {
        "user_prompt": "What is machine learning and how is it used in everyday life?"
    }
    
    # Run the workflow
    print("\n🚀 Starting workflow...\n")
    result = await flow.run_async(initial_input)
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    final_output = result.get("final_output", {})
    print(f"\n📝 Question: {final_output.get('question', 'N/A')}")
    print(f"\n💡 Answer:\n{final_output.get('answer', 'N/A')}")
    print(f"\n📊 Metadata: {final_output.get('metadata', {})}")
    
    print("\n✅ Workflow completed successfully!")
    print("\n💾 Telemetry data has been uploaded to Agora Cloud")
    print("   View your workflow at: https://your-agora-dashboard.com")


# ============================================================================
# COLAB EXECUTION
# ============================================================================

if __name__ == "__main__":
    # For Google Colab, we need nest_asyncio to handle event loops
    try:
        import nest_asyncio
        nest_asyncio.apply()
        print("✓ Applied nest_asyncio for Colab compatibility\n")
    except ImportError:
        print("⚠ nest_asyncio not found. Install with: pip install nest-asyncio\n")
    
    # Run the workflow
    asyncio.run(main())
