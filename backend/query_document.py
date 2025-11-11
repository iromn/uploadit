import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from typing import List

# -------------------- Load env --------------------
load_dotenv()

# -------------------- Pinecone --------------------
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = "doc-bot-v3"
index = pc.Index(INDEX_NAME)

# -------------------- Embedding model --------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------- OpenAI client --------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------- Utility --------------------
def cosine_similarity(a: List[float], b: List[float]) -> float:
    from math import sqrt
    return sum(x*y for x, y in zip(a, b)) / (sqrt(sum(x*x for x in a)) * sqrt(sum(y*y for y in b)) + 1e-10)


# -------------------- Main function --------------------
def ask_question(query: str, session_id: str) -> str:
    """
    Query Pinecone for a given session, rank by similarity, and return LLM answer.
    """
    try:
        # Encode the query
        query_vector = model.encode(query).tolist()

        # Query Pinecone for session-specific vectors
        results = index.query(
            vector=query_vector,
            top_k=5,
            include_metadata=True,
            filter={"session_id": {"$eq": session_id}}  # only fetch vectors for this session
        )

        if not results.matches:
            return "No relevant context found for this session."

        # Combine top matches
        context = " ".join([match.metadata.get("text", "") for match in results.matches])

        # Prompt for LLM
        prompt = f"""
You are a helpful assistant. Answer the question based on the context below.

Context:
{context}

Question:
{query}

Answer:
"""

        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You answer user questions based on provided context."},
                {"role": "user", "content": prompt.strip()}
            ]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"❌ Error in ask_question: {e}")
        return "An error occurred while generating the answer."
