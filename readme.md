# <img src="./frontend/public/uploadit.png" alt="UploadiT Logo" width="40" /> <span style="position: relative; top: -7px">UploadiT</span>


A **FastAPI + Pinecone + Next.js** application that allows users to upload documents (PDF, DOCX, TXT) and ask questions based on the document content. Each user session has ephemeral vector embeddings stored in **Pinecone**, allowing session-specific context and automatic cleanup.

---

## Features

- ✅ Upload documents (PDF, DOCX, TXT) and automatically extract text.
- ✅ Chunk and embed document content using **SentenceTransformers**.
- ✅ Store vectors in **Pinecone** for session-specific question answering.
- ✅ Ask natural language questions about uploaded documents.
- ✅ Session-based ephemeral memory: each session’s embeddings are isolated.
- ✅ Clear session embeddings manually or automatically after inactivity.
- ✅ Automatic session expiration to clean up abandoned sessions and disk storage.
- ✅ Frontend built with **Next.js**, providing an interactive chat interface.

---

## Tech Stack

- **Backend:** FastAPI, Pinecone, SentenceTransformers, OpenAI (optional for LLM answers)
- **Frontend:** Next.js (React)
- **Vector Database:** Pinecone
- **Document Parsing:** PyPDF2 (PDF), python-docx (DOCX)
- **Environment Management:** dotenv

---

## Setup Instructions

### 1. Clone the Repository

```
git clone https://github.com/iromn/uploadit.git
cd doc-qa-bot
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

## Usage

 - Open the frontend in your browser.
 - Create a new session → receive a session_id.
 - Upload a PDF, DOCX, or TXT document.
 - Ask questions related to the uploaded document.
 - Clear session embeddings manually via the "Clear Session" button or let them expire automatically.