"""
Multi-Node Workflow Example with LLM Calls
This demonstrates a workflow with multiple nodes, showing data flow and execution timing.
"""
import asyncio
import os
from agora.agora_tracer import TracedAsyncFlow, agora_node, init_agora
from openai import AsyncOpenAI

# Initialize Agora
init_agora(app_name="ContentPipeline", export_to_console=False, enable_cloud_upload=True)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@agora_node(name="PrepareData")
async def prepare_data(shared):
    """Prepare initial data for processing"""
    await asyncio.sleep(0.2)
    data = {
        "topic": "artificial intelligence",
        "requirements": ["concise", "informative", "engaging"],
        "max_words": 50
    }
    shared["prepared_data"] = data
    print(f"✓ Data prepared: {data['topic']}")
    # Return None to continue to next node (default routing)
    return None

@agora_node(name="GenerateContent")
async def generate_content(shared):
    """Generate content using OpenAI"""
    data = shared["prepared_data"]
    
    prompt = f"""Write a {data['max_words']}-word summary about {data['topic']}.
    Make it {', '.join(data['requirements'])}.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful content writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    content = response.choices[0].message.content
    shared["generated_content"] = content
    shared["word_count"] = len(content.split())
    print(f"✓ Content generated: {len(content.split())} words")
    return None

@agora_node(name="AnalyzeContent")
async def analyze_content(shared):
    """Analyze the generated content"""
    await asyncio.sleep(0.3)
    content = shared["generated_content"]
    
    analysis = {
        "word_count": len(content.split()),
        "character_count": len(content),
        "sentence_count": content.count('.') + content.count('!') + content.count('?'),
        "has_keywords": any(kw in content.lower() for kw in ["ai", "artificial", "intelligence", "machine", "learning"])
    }
    
    shared["analysis"] = analysis
    print(f"✓ Content analyzed: {analysis['word_count']} words, {analysis['sentence_count']} sentences")
    return None

@agora_node(name="QualityCheck")
async def quality_check(shared):
    """Check content quality using LLM"""
    content = shared["generated_content"]
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a content quality reviewer. Rate content 1-10 and give brief feedback."},
            {"role": "user", "content": f"Rate this content:\n\n{content}"}
        ],
        temperature=0.3,
        max_tokens=100
    )
    
    quality_feedback = response.choices[0].message.content
    shared["quality_feedback"] = quality_feedback
    print(f"✓ Quality checked: {quality_feedback[:50]}...")
    return None

@agora_node(name="FormatOutput")
async def format_output(shared):
    """Format the final output"""
    await asyncio.sleep(0.2)
    content = shared["generated_content"]
    analysis = shared["analysis"]
    quality = shared["quality_feedback"]
    
    output = {
        "content": content,
        "statistics": analysis,
        "quality_review": quality,
        "status": "completed"
    }
    
    shared["final_output"] = output
    print(f"✓ Output formatted successfully")
    return output  # Return final output

async def main():
    print("🚀 Starting Multi-Node Content Pipeline...")
    print("=" * 70)
    
    # Create workflow
    flow = TracedAsyncFlow("ContentPipeline")
    
    # Build pipeline using >> operator: prepare >> generate >> analyze >> quality >> format
    flow.start(prepare_data) >> generate_content >> analyze_content >> quality_check >> format_output
    
    # Execute workflow
    result = await flow.run_async({})
    
    print("\n" + "=" * 70)
    print("✅ Workflow completed!")
    print("=" * 70)
    print("\n📊 Final Output:")
    print(f"Content: {result['content'][:100]}...")
    print(f"Word Count: {result['statistics']['word_count']}")
    print(f"Sentences: {result['statistics']['sentence_count']}")
    print(f"Quality Review: {result['quality_review'][:80]}...")
    print("\n💡 Check the monitoring page to see the workflow graph!")
    print("   → http://localhost:5173/monitoring")
    print("   → Click 'Executions' tab")
    print("   → Click 'View Details' on the latest execution")
    print("   → Click 'Workflow' tab to see the graph!")
    print("   → Click on nodes to see their code and data!")

if __name__ == "__main__":
    asyncio.run(main())
