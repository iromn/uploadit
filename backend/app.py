import os
import uuid
import glob
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
from docx import Document
from embed_document import embed_document, clear_session_embeddings
from query_document import ask_question
from threading import Thread

# -------------------- Initialize --------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict later if needed
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------- Session Storage --------------------
# Stores last activity timestamp for sessions
# Format: { session_id: last_activity_timestamp }
session_activity = {}
SESSION_TTL = 60 * 60  # 1 hour in seconds

# -------------------- Request Models --------------------
class QuestionRequest(BaseModel):
    session_id: str
    question: str

# -------------------- Utilities --------------------
def load_pdf_text(pdf_path: str) -> str:
    pdf = PdfReader(pdf_path)
    text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

def chunk_text(text: str, chunk_size: int = 1000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# -------------------- Session Management --------------------
def update_session_activity(session_id: str):
    session_activity[session_id] = time.time()

def clear_temp_files(session_id: str):
    files = glob.glob(f"temp_uploads/{session_id}-*")
    for file_path in files:
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

def cleanup_expired_sessions():
    """Background thread to clear expired sessions periodically."""
    while True:
        now = time.time()
        expired_sessions = [
            sid for sid, ts in session_activity.items()
            if now - ts > SESSION_TTL
        ]
        for sid in expired_sessions:
            try:
                clear_session_embeddings(sid)
                clear_temp_files(sid)
                del session_activity[sid]
                print(f"🗑️ Auto-cleared expired session {sid}")
            except Exception as e:
                print(f"Error clearing expired session {sid}: {e}")
        time.sleep(60)  # run every 1 minute

# Start background cleanup thread
Thread(target=cleanup_expired_sessions, daemon=True).start()

# -------------------- Endpoints --------------------
@app.get("/")
def root():
    return {"message": "✅ Doc-QA backend with Pinecone and auto session expiration running"}

# Create a new session
@app.post("/session")
def create_session():
    session_id = str(uuid.uuid4())
    update_session_activity(session_id)
    return {"session_id": session_id}

# Upload and embed document for a session
@app.post("/upload")
async def upload_file(session_id: str = Form(...), file: UploadFile = File(...)):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    update_session_activity(session_id)

    try:
        # Save temporarily
        upload_dir = "temp_uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{session_id}-{file.filename}")
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Embed the document in Pinecone for this session
        embed_document(file_path, session_id)

        return {"success": True, "message": f"{file.filename} uploaded and embedded for session {session_id}"}
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {e}")

# Ask question using session-specific vectors
@app.post("/ask")
def ask_question_api(request: QuestionRequest):
    if not request.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    if not request.question.strip():
        return {"answer": "Please ask a valid question."}

    update_session_activity(request.session_id)

    answer = ask_question(request.question, request.session_id)
    return {"answer": answer}

# Clear all vectors and files for a session
@app.post("/clear_session")
def clear_session(session_id: str):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    try:
        clear_session_embeddings(session_id)
        clear_temp_files(session_id)
        if session_id in session_activity:
            del session_activity[session_id]

        return {
            "success": True,
            "message": f"Session {session_id} cleared: vectors + uploaded files removed.",
        }
    except Exception as e:
        print(f"❌ Error clearing session: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear session")
