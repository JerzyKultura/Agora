# ============================================================================
# RAG WITH AGORA + TELEMETRY
# ============================================================================

# Install dependencies
!pip install --upgrade pymilvus openai requests tqdm
!pip install --force-reinstall git+https://github.com/JerzyKultura/Agora.git
!pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-openai
!pip install pymilvus[milvus_lite]

import os
import json
from glob import glob
from tqdm import tqdm
from openai import OpenAI
from pymilvus import MilvusClient

# Agora imports
from agora.telemetry import AuditLogger, AuditedNode, AuditedFlow

# OpenTelemetry setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
OpenAIInstrumentor().instrument()

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = ""

# Download and extract data (only run once)
!wget -q https://github.com/milvus-io/milvus-docs/releases/download/v2.4.6-preview/milvus_docs_2.4.x_en.zip
!unzip -q milvus_docs_2.4.x_en.zip -d milvus_docs

# ============================================================================
# AGORA RAG WORKFLOW NODES
# ============================================================================

class DocumentLoader(AuditedNode):
    """Load and split documents from markdown files"""

    def prep(self, shared):
        return "milvus_docs/en/faq/*.md"

    def exec(self, file_pattern):
        text_lines = []
        files_processed = 0

        for file_path in glob(file_pattern, recursive=True):
            with open(file_path, "r") as file:
                file_text = file.read()
            text_lines += file_text.split("# ")
            files_processed += 1

        return {"text_lines": text_lines, "files_processed": files_processed}

    def post(self, shared, prep_res, exec_res):
        shared["documents"] = exec_res["text_lines"]
        print(f"Loaded {len(exec_res['text_lines'])} text chunks from {exec_res['files_processed']} files")
        return "embed"

class EmbeddingGenerator(AuditedNode):
    """Generate embeddings for text chunks using OpenAI"""

    def prep(self, shared):
        self.openai_client = OpenAI()
        return shared["documents"]

    def exec(self, documents):
        embeddings_data = []

        for i, text in enumerate(tqdm(documents, desc="Creating embeddings")):
            if text.strip():  # Skip empty texts
                embedding = self.openai_client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                ).data[0].embedding

                embeddings_data.append({
                    "id": i,
                    "vector": embedding,
                    "text": text
                })

        return embeddings_data

    def post(self, shared, prep_res, exec_res):
        shared["embeddings_data"] = exec_res
        shared["embedding_dim"] = len(exec_res[0]["vector"]) if exec_res else 0
        print(f"Generated {len(exec_res)} embeddings, dimension: {shared['embedding_dim']}")
        return "store"

class MilvusStorer(AuditedNode):
    """Store embeddings in Milvus vector database"""

    def prep(self, shared):
        self.milvus_client = MilvusClient(uri="./milvus_demo.db")
        self.collection_name = "rag_collection"

        # Setup collection
        if self.milvus_client.has_collection(self.collection_name):
            self.milvus_client.drop_collection(self.collection_name)

        self.milvus_client.create_collection(
            collection_name=self.collection_name,
            dimension=shared["embedding_dim"],
            metric_type="IP"
        )

        return shared["embeddings_data"]

    def exec(self, embeddings_data):
        self.milvus_client.insert(
            collection_name=self.collection_name,
            data=embeddings_data
        )
        return len(embeddings_data)

    def post(self, shared, prep_res, exec_res):
        shared["milvus_client"] = self.milvus_client
        shared["collection_name"] = self.collection_name
        print(f"Stored {exec_res} vectors in Milvus collection")
        return "ready"

# ============================================================================
# RAG QUERY NODES
# ============================================================================

class QueryEmbedder(AuditedNode):
    """Convert query to embedding vector"""

    def prep(self, shared):
        self.openai_client = OpenAI()
        return shared.get("question", "How is data stored in milvus?")

    def exec(self, question):
        embedding = self.openai_client.embeddings.create(
            input=question,
            model="text-embedding-3-small"
        ).data[0].embedding

        return embedding

    def post(self, shared, prep_res, exec_res):
        shared["query_embedding"] = exec_res
        shared["question"] = prep_res
        print(f"Generated embedding for query: {prep_res}")
        return "search"

class VectorSearcher(AuditedNode):
    """Search Milvus for similar documents"""

    def prep(self, shared):
        return {
            "milvus_client": shared["milvus_client"],
            "collection_name": shared["collection_name"],
            "query_embedding": shared["query_embedding"]
        }

    def exec(self, search_params):
        search_res = search_params["milvus_client"].search(
            collection_name=search_params["collection_name"],
            data=[search_params["query_embedding"]],
            limit=3,
            search_params={"metric_type": "IP", "params": {}},
            output_fields=["text"]
        )

        retrieved_docs = [
            (res["entity"]["text"], res["distance"])
            for res in search_res[0]
        ]

        return retrieved_docs

    def post(self, shared, prep_res, exec_res):
        shared["retrieved_docs"] = exec_res
        print(f"Retrieved {len(exec_res)} relevant documents")
        print(f"Top match distance: {exec_res[0][1]:.3f}" if exec_res else "No results")
        return "generate"

class ResponseGenerator(AuditedNode):
    """Generate final RAG response using LLM"""

    def prep(self, shared):
        self.openai_client = OpenAI()

        # Build context from retrieved documents
        context = "\n".join([doc[0] for doc in shared["retrieved_docs"]])

        return {
            "question": shared["question"],
            "context": context
        }

    def exec(self, rag_input):
        SYSTEM_PROMPT = """
        Human: You are an AI assistant. You are able to find answers to the questions from the contextual passage snippets provided.
        """

        USER_PROMPT = f"""
        Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.
        <context>
        {rag_input["context"]}
        </context>
        <question>
        {rag_input["question"]}
        </question>
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT},
            ],
        )

        return response.choices[0].message.content

    def post(self, shared, prep_res, exec_res):
        shared["final_answer"] = exec_res
        print("Generated RAG response:")
        print("-" * 50)
        print(exec_res)
        print("-" * 50)
        return "complete"

# ============================================================================
# BUILD AND RUN RAG WORKFLOWS
# ============================================================================

def build_knowledge_base():
    """Build the knowledge base using Agora workflow"""

    # Create audit logger
    logger = AuditLogger("rag-indexing")

    # Create nodes
    loader = DocumentLoader("DocumentLoader", logger)
    embedder = EmbeddingGenerator("EmbeddingGenerator", logger)
    storer = MilvusStorer("MilvusStorer", logger)

    # Create workflow
    flow = AuditedFlow("RAGIndexing", logger)
    flow.start(loader)

    # Build pipeline
    loader - "embed" >> embedder
    embedder - "store" >> storer

    # Run indexing
    shared = {}
    flow.run(shared)

    # Show audit results
    print(f"\nIndexing Audit Summary: {logger.get_summary()}")
    logger.save_json("rag_indexing_audit.json")

    return shared

def query_knowledge_base(shared, question="How is data stored in milvus?"):
    """Query the knowledge base using Agora workflow"""

    # Create audit logger
    logger = AuditLogger("rag-query")

    # Create nodes
    query_embedder = QueryEmbedder("QueryEmbedder", logger)
    searcher = VectorSearcher("VectorSearcher", logger)
    generator = ResponseGenerator("ResponseGenerator", logger)

    # Create workflow
    flow = AuditedFlow("RAGQuery", logger)
    flow.start(query_embedder)

    # Build pipeline
    query_embedder - "search" >> searcher
    searcher - "generate" >> generator

    # Add question and existing state
    shared["question"] = question

    # Run query
    flow.run(shared)

    # Show audit results
    print(f"\nQuery Audit Summary: {logger.get_summary()}")
    logger.save_json("rag_query_audit.json")

    return shared

# ============================================================================
# RUN THE COMPLETE RAG SYSTEM
# ============================================================================

# ============================================================================
# INTERACTIVE RAG CHAT
# ============================================================================

def interactive_rag_chat(shared_state):
    """Interactive chat with the RAG system"""

    print("\n" + "="*60)
    print("INTERACTIVE RAG CHAT")
    print("="*60)
    print("Ask questions about Milvus! Type 'exit' to quit.")
    print("-"*60)

    while True:
        question = input("\nYour question: ").strip()

        if question.lower() in ['exit', 'quit', 'stop']:
            print("Thanks for using RAG with Agora!")
            break

        if not question:
            print("Please enter a question.")
            continue

        print(f"\nProcessing: {question}")
        print("-" * 40)

        # Query the knowledge base
        query_knowledge_base(shared_state, question)

def run_full_rag_demo():
    """Run the complete RAG demo with Agora + Telemetry"""

    print("=" * 60)
    print("RAG WITH AGORA + TELEMETRY DEMO")
    print("=" * 60)

    # Step 1: Build knowledge base
    print("\n1. Building Knowledge Base...")
    shared_state = build_knowledge_base()

    # Step 2: Demo queries
    print("\n2. Running Demo Queries...")
    query_knowledge_base(shared_state, "How is data stored in milvus?")

    print("\n3. Try another query...")
    query_knowledge_base(shared_state, "What are the different types of indexes in Milvus?")

    # Step 3: Interactive mode
    print("\n4. Starting Interactive Mode...")
    interactive_rag_chat(shared_state)

    print("\nRAG Demo Complete!")
    print("Check the audit JSON files for detailed execution logs.")

# Run the demo
print("Ready to run RAG with Agora!")
print("Execute: run_full_rag_demo()")

# Or run just the interactive chat after building knowledge base:
# print("To run interactive chat only:")
# print("shared_state = build_knowledge_base()")
# print("interactive_rag_chat(shared_state)")

run_full_rag_demo()
