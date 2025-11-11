import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Use new index name
index_name = "doc-bot-v3"

# Delete old index if it exists
if index_name in pc.list_indexes().names():
    pc.delete_index(index_name)
    print(f"🗑️ Deleted old index '{index_name}'")

# Create new index
pc.create_index(
    name=index_name,
    dimension=384,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

print(f"✅ Created new index '{index_name}' with dimension 384")
