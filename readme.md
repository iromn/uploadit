# <img src="./frontend/public/uploadit.png" alt="UploadiT Logo" width="40" /> <span style="position: relative; top: -7px">UploadiT</span>


A **FastAPI + Pinecone + Next.js** application that allows users to upload and query multiple documents (PDF, DOCX, TXT) using semantic search and conversational AI.
Each user session maintains isolated embeddings stored in **Pinecone**, ensuring secure, session-specific context with automatic cleanup.

---

## 🚀 Features

- ✅ Upload one or more documents (PDF, DOCX, TXT) — up to 5 per session.
- ✅ Automatically extract, chunk, and embed document content using **SentenceTransformers**.
- ✅ Store vectors in **Pinecone** for fast semantic search per session.
- ✅ Ask **natural language questions** based on all uploaded documents combined.
- ✅ Session-based ephemeral memory — each session’s data is isolated.
- ✅ Manual and automatic session cleanup for expired or inactive sessions.
- ✅ Frontend built with **Next.js**, providing an interactive chat interface.
- ✅ Improved UX:
    - Upload button shows loader and disables during upload.
    - Sidebar displays uploaded documents with “Upload More” option (max 5).

---

## 🧩 Tech Stack

- **Backend:** FastAPI, Pinecone, SentenceTransformers, OpenAI (optional for LLM answers)
- **Frontend:** Next.js (React)
- **Vector Database:** Pinecone
- **Document Parsing:** PyPDF2 (PDF), python-docx (DOCX)
- **Environment Management:** dotenv

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```
git clone https://github.com/iromn/uploadit.git
```

### 2. Install Backend Dependencies

```
cd backend
python -m venv venv

source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a .env file in the backend folder:

```
PINECONE_API_KEY=your_pinecone_api_key
OPENAI_API_KEY=your_openai_api_key
PINECONE_ENVIRONMENT=us-east-1-aws
```

### 4. Reset or Create Pinecone Index

```
python reset_index.py
```

### 5. Start the Backend

```
uvicorn app:app --reload
```
Backend will run at: http://localhost:8000

### 6. Setup Frontend

```
cd ../frontend
npm install
npm run dev
```

## 💡 Usage Guide

 - Open the app in your browser.
 - A new session will automatically be created.
 - Upload one or more documents (PDF, DOCX, or TXT).
 - Wait for the upload loader to finish — your files will appear in the sidebar.
 - Ask natural-language questions related to the uploaded documents.
 - Upload additional documents at any time (max 5 per session).
 - Use “Clear Session” to reset and start fresh.

## 🧠 Example Use Cases
 - Research paper Q&A
 - Legal or policy document search
 - Knowledge base assistant
 - Study material summarization
 - Multi-document comparison

## 📸 UI Enhancements
 - Modern chat layout with message bubbles
 - Visual feedback for uploading state
 - File list panel showing uploaded documents
 - Dynamic upload button state (Upload → Uploading…)
 - File input clears automatically after successful upload