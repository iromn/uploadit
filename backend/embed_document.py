import os
from pinecone import Pinecone, ServerlessSpec
from PyPDF2 import PdfReader
from docx import Document
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# -------------------- Initialize Pinecone --------------------
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = "doc-bot-v3"  # new index for testing

# Create index if it doesn't exist
if INDEX_NAME not in pc.list_indexes().names():
    print(f"📦 Creating Pinecone index '{INDEX_NAME}'...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

index = pc.Index(INDEX_NAME)

# Load embedding model once
print("🔍 Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------- Text extraction helpers --------------------
def load_pdf_text(pdf_path):
    pdf = PdfReader(pdf_path)
    text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text


def load_docx_text(docx_path):
    doc = Document(docx_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


# -------------------- Chunking --------------------
def chunk_text(text, chunk_size=1000):
    """Split text into smaller chunks"""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


# -------------------- Embedding Helpers --------------------
def embed_text_chunks(chunks, session_id: str, prefix="chunk"):
    """
    Embed a list of text chunks and upload to Pinecone.
    """
    if not chunks:
        print("⚠️ No chunks to embed.")
        return

    vectors = []
    for i, chunk in enumerate(chunks):
        vector = model.encode(chunk).tolist()
        vectors.append((
            f"{session_id}-{prefix}-{i}",
            vector,
            {"text": chunk, "session_id": session_id}
        ))

    # Upsert in batches
    batch_size = 50
    for i in range(0, len(vectors), batch_size):
        index.upsert(vectors[i:i + batch_size])

    print(f"✅ Uploaded {len(chunks)} chunks for session {session_id}")


def embed_text(text, session_id: str, prefix="chunk"):
    """Convenience wrapper for embedding full text."""
    chunks = chunk_text(text)
    embed_text_chunks(chunks, session_id, prefix=prefix)


# -------------------- File-based embedding --------------------
def embed_pdf(pdf_path, session_id: str):
    text = load_pdf_text(pdf_path)
    embed_text(text, session_id, prefix=os.path.basename(pdf_path))


def embed_document(data, session_id: str):
    """
    Flexible entry point:
    - If `data` is a path to a file, detect file type and process it.
    - If `data` is already a list of text chunks, embed them directly.
    - If `data` is a single string, chunk and embed it directly.
    """
    # Case 1: list of chunks already
    if isinstance(data, list):
        print(f"🧩 Embedding pre-chunked text for session {session_id}")
        embed_text_chunks(data, session_id, prefix="manual")
        return

    # Case 2: plain text
    if isinstance(data, str) and not os.path.exists(data):
        print(f"🧠 Embedding raw text input for session {session_id}")
        embed_text(data, session_id, prefix="manual")
        return

    # Case 3: file path
    if not os.path.exists(data):
        raise ValueError(f"Invalid file path: {data}")

    file_path = data
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        print(f"📄 Embedding PDF: {file_path}")
        embed_pdf(file_path, session_id)
    elif ext == ".txt":
        print(f"📜 Embedding TXT: {file_path}")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        embed_text(text, session_id, prefix=os.path.basename(file_path))
    elif ext == ".docx":
        print(f"📝 Embedding DOCX: {file_path}")
        text = load_docx_text(file_path)
        embed_text(text, session_id, prefix=os.path.basename(file_path))
    else:
        raise ValueError(f"Unsupported file format: {ext}")


# -------------------- Clear session embeddings --------------------
def clear_session_embeddings(session_id: str):
    """
    Delete all vectors for a session using metadata filter.
    """
    print(f"🗑️ Clearing embeddings for session {session_id}...")
    index.delete(delete_all=False, filter={"session_id": {"$eq": session_id}})
    print(f"✅ Cleared embeddings for session {session_id}")
