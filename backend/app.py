import os
import uuid
import glob
import time
from threading import Thread
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
from docx import Document
from embed_document import embed_document, clear_session_embeddings
from query_document import ask_question

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
# Stores session data:
# { session_id: { "last_activity": timestamp, "files": [filenames] } }
session_activity = {}
SESSION_TTL = 60 * 60  # 1 hour
MAX_FILES_PER_SESSION = 5  # configurable limit

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
    """Update or initialize session timestamp."""
    if session_id not in session_activity:
        session_activity[session_id] = {"last_activity": time.time(), "files": []}
    else:
        session_activity[session_id]["last_activity"] = time.time()

def clear_temp_files(session_id: str):
    """Delete temporary files linked to a session."""
    files = glob.glob(f"temp_uploads/{session_id}-*")
    for file_path in files:
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"⚠️ Failed to delete {file_path}: {e}")

def cleanup_expired_sessions():
    """Background thread to auto-clear expired sessions."""
    while True:
        now = time.time()
        expired = [
            sid for sid, data in session_activity.items()
            if now - data["last_activity"] > SESSION_TTL
        ]
        for sid in expired:
            try:
                clear_session_embeddings(sid)
                clear_temp_files(sid)
                del session_activity[sid]
                print(f"🗑️ Auto-cleared expired session {sid}")
            except Exception as e:
                print(f"⚠️ Error clearing expired session {sid}: {e}")
        time.sleep(60)

# Start cleanup background thread
Thread(target=cleanup_expired_sessions, daemon=True).start()

# -------------------- Endpoints --------------------
@app.get("/")
def root():
    return {"message": "✅ Doc-QA backend with Pinecone and multi-file upload running"}

# Create a new session
@app.post("/session")
def create_session():
    session_id = str(uuid.uuid4())
    update_session_activity(session_id)
    return {"session_id": session_id}

# Upload and embed one or more documents for a session
@app.post("/upload")
async def upload_files(session_id: str = Form(...), files: list[UploadFile] = File(...)):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    update_session_activity(session_id)
    session_data = session_activity[session_id]

    # Enforce file limit per session
    already_uploaded = len(session_data["files"])
    remaining = MAX_FILES_PER_SESSION - already_uploaded
    if len(files) > remaining:
        raise HTTPException(
            status_code=400,
            detail=f"File limit exceeded. You can upload {remaining} more file(s)."
        )

    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)

    uploaded_filenames = []
    for file in files:
        filename = file.filename
        ext = filename.lower().split(".")[-1]

        if ext not in ["pdf", "docx", "txt"]:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, DOCX, or TXT files are supported."
            )

        file_path = os.path.join(upload_dir, f"{session_id}-{filename}")
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Extract text based on file type
        if ext == "pdf":
            text = load_pdf_text(file_path)
        elif ext == "docx":
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as t:
                text = t.read()
        else:
            text = ""

        # Chunk and embed document text
        chunks = chunk_text(text)
        embed_document(chunks, session_id)

        uploaded_filenames.append(filename)
        session_data["files"].append(filename)

    # Update timestamp
    update_session_activity(session_id)

    return {
        "success": True,
        "session_id": session_id,
        "uploaded_files": session_data["files"],
        "message": f"{len(uploaded_filenames)} file(s) uploaded and embedded successfully."
    }

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

# Get uploaded files for session
@app.get("/session_files")
def get_session_files(session_id: str):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    files = session_activity.get(session_id, {}).get("files", [])
    return {"session_id": session_id, "files": files}

# Clear session (embeddings + temp files)
@app.post("/clear_session")
def clear_session(session_id: str):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    try:
        # clear_session_embeddings(session_id) #This is to clear the vector from the index.
        clear_temp_files(session_id)
        if session_id in session_activity:
            del session_activity[session_id]

        return {"success": True, "message": f"Session {session_id} cleared successfully."}
    except Exception as e:
        print(f"❌ Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {e}")
