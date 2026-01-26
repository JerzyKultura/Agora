# ---------------------------------------------------------
# 📋 COPY & PASTE THIS CELL INTO YOUR COLAB NOTEBOOK
# ---------------------------------------------------------

# 1. Install Qdrant Client (if not already installed)
!pip install qdrant-client

import os
from qdrant_client import QdrantClient

# 2. Setup (Pre-filled with your keys)
QDRANT_URL = "https://f99616d9-4f33-4974-bc51-361915459d7a.us-east4-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.CvolEUftQXtDFyKN63kOa180Jl87wrUVj78CosBmd9M"

print("\n🔍 INSPECTING QDRANT CLUSTER...")
print(f"Target: {QDRANT_URL}")

try:
    # 3. Connect
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # 4. List Collections
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]
    print(f"📂 Found Collections: {collection_names}")

    # 5. Inspect Data (First 5 items from 'agora_collection')
    TARGET_COLLECTION = "agora_collection"
    
    if TARGET_COLLECTION in collection_names:
        print(f"\n📄 Peeking at data in '{TARGET_COLLECTION}':")
        results, next_page = client.scroll(
            collection_name=TARGET_COLLECTION,
            limit=5,
            with_payload=True,
            with_vectors=False
        )
        
        if not results:
            print("   (Collection is empty)")
        
        for point in results:
            print(f"   🔹 ID: {point.id}")
            print(f"      Payload: {point.payload}")
            print("-" * 40)
    else:
        print(f"\n⚠️ Collection '{TARGET_COLLECTION}' not found. Did you run the chatbot demo yet?")

except Exception as e:
    print(f"\n❌ Connection Failed: {e}")
