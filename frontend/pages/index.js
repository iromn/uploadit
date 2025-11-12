"use client";
import { useState, useEffect, useRef } from "react";
import axios from "axios";
const API_BASE = process.env.UPLOADIT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [files, setFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [chat, setChat] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const fileInputRef = useRef(null);
  const MAX_FILES = 5;

  // -------------------- Create session on load --------------------
  useEffect(() => {
    const createSession = async () => {
      try {
        const res = await axios.post(`${API_BASE}/session`);
        setSessionId(res.data.session_id);
        console.log("Session created:", res.data.session_id);
      } catch (err) {
        console.error("Error creating session:", err);
        alert("Error creating session. Please refresh the page.");
      }
    };
    createSession();
  }, []);

  // -------------------- Upload one or more files --------------------
  const handleUpload = async () => {
    if (files.length === 0) {
      alert("Please select one or more PDF files first!");
      return;
    }
    if (!sessionId) {
      alert("Session not initialized yet.");
      return;
    }

    const totalFiles = uploadedFiles.length + files.length;
    if (totalFiles > MAX_FILES) {
      alert(`You can only upload up to ${MAX_FILES} files per session.`);
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("session_id", sessionId);
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      const res = await axios.post(`${API_BASE}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (res.data.success) {
        alert(res.data.message);
        setUploadedFiles(res.data.uploaded_files);
        setFiles([]);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || "Error uploading files.");
    } finally {
      setUploading(false);
    }
  };

  // -------------------- Fetch uploaded files --------------------
  const fetchSessionFiles = async () => {
    if (!sessionId) return;
    try {
      const res = await axios.get(`${API_BASE}/session_files`, {
        params: { session_id: sessionId },
      });
      setUploadedFiles(res.data.files || []);
    } catch (err) {
      console.error("Error fetching session files:", err);
    }
  };

  useEffect(() => {
    if (sessionId) fetchSessionFiles();
  }, [sessionId]);

  // -------------------- Ask a question --------------------
  const sendQuestion = async () => {
    if (!input.trim()) return;
    if (!sessionId) {
      alert("Session not initialized yet.");
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/ask`, {
        session_id: sessionId,
        question: input,
      });
      setChat((prev) => [...prev, { question: input, answer: res.data.answer }]);
      setInput("");
    } catch (err) {
      console.error(err);
      alert("Error connecting to backend.");
    }
    setLoading(false);
  };

  // -------------------- Clear session --------------------
  const clearSession = async () => {
    if (!sessionId) return;
    try {
      await axios.post(`${API_BASE}/clear_session`, null, {
        params: { session_id: sessionId },
      });
      setChat([]);
      setUploadedFiles([]);
      setFiles([]);
      alert("Session cleared!");
    } catch (err) {
      console.error(err);
      alert("Error clearing session.");
    }
  };

  // -------------------- UI --------------------
  return (
    <div
      style={{
        maxWidth: 900,
        margin: "50px auto",
        fontFamily: "Inter, Arial, sans-serif",
        display: "flex",
        gap: 20,
      }}
    >
      {/* Left: Chat area */}
      <div
        style={{
          flex: 2,
          display: "flex",
          flexDirection: "column",
          height: "80vh",
        }}
      >
        <h1 style={{ textAlign: "center", marginBottom: 20 }}>
          <img
            src="/uploadit.png"
            alt="UploadiT Logo"
            style={{ height: 50, verticalAlign: "middle" }}
          />{" "}
          UploadiT
        </h1>

        <div
          style={{
            border: "1px solid #ddd",
            borderRadius: 12,
            padding: 15,
            flexGrow: 1,
            overflowY: "auto",
            backgroundColor: "#fafafa",
            boxShadow: "0 4px 10px rgba(0,0,0,0.05)",
          }}
        >
          {chat.map((item, idx) => (
            <div key={idx} style={{ marginBottom: 20 }}>
              {/* User message */}
              <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8 }}>
                <div
                  style={{
                    background: "#0070f3",
                    color: "#fff",
                    padding: "10px 15px",
                    borderRadius: "18px 18px 4px 18px",
                    maxWidth: "70%",
                    fontSize: "15px",
                    lineHeight: "1.5",
                    wordBreak: "break-word",
                  }}
                >
                  {item.question}
                </div>
              </div>

              {/* Bot answer */}
              <div style={{ display: "flex", justifyContent: "flex-start" }}>
                <div
                  style={{
                    background: "#e9e9eb",
                    color: "#222",
                    padding: "10px 15px",
                    borderRadius: "18px 18px 18px 4px",
                    maxWidth: "70%",
                    fontSize: "15px",
                    lineHeight: "1.5",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {item.answer}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div
              style={{
                textAlign: "left",
                color: "#555",
                fontStyle: "italic",
                marginTop: 10,
              }}
            >
              Bot is typing...
            </div>
          )}
        </div>

        {/* Input box */}
        <div style={{ display: "flex", marginTop: 15 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            style={{
              flex: 1,
              padding: "12px 15px",
              fontSize: 16,
              borderRadius: 8,
              border: "1px solid #ccc",
              outline: "none",
            }}
            placeholder="Ask a question..."
            onKeyDown={(e) => e.key === "Enter" && sendQuestion()}
          />
          <button
            onClick={sendQuestion}
            style={{
              marginLeft: 10,
              padding: "12px 20px",
              fontSize: 16,
              borderRadius: 8,
              backgroundColor: "#0070f3",
              color: "#fff",
              border: "none",
              cursor: "pointer",
            }}
          >
            Ask
          </button>
          <button
            onClick={clearSession}
            style={{
              marginLeft: 10,
              padding: "12px 20px",
              fontSize: 16,
              borderRadius: 8,
              backgroundColor: "#f44336",
              color: "#fff",
              border: "none",
              cursor: "pointer",
            }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Right: File upload area */}
      <div
        style={{
          flex: 1,
          border: "1px solid #ddd",
          borderRadius: 12,
          padding: 20,
          background: "#fff",
          height: "80vh",
          overflowY: "auto",
        }}
      >
        <h3 style={{ marginBottom: 15 }}>📄 Uploaded Documents</h3>
        <p style={{ color: "#777", fontSize: 14, marginBottom: 10 }}>
          Supported formats: PDF, TXT, DOCX
        </p>
        {uploadedFiles.length === 0 ? (
          <p style={{ color: "#555" }}>No documents uploaded yet.</p>
        ) : (
          <ul style={{ paddingLeft: 20, color: "#333" }}>
            {uploadedFiles.map((name, i) => (
              <li key={i}>{name}</li>
            ))}
          </ul>
        )}

        <hr style={{ margin: "20px 0" }} />

        <p style={{ fontSize: 14, color: "#666" }}>
          You can upload up to {MAX_FILES} PDFs per session.
        </p>

        <input
          type="file"
          accept=".pdf,.txt,.docx"
          multiple
          onChange={(e) => setFiles(Array.from(e.target.files))}
          disabled={uploading}
          style={{ marginBottom: 15 }}
        />

        <button
          onClick={handleUpload}
          disabled={uploading}
          style={{
            width: "100%",
            padding: "12px 0",
            fontSize: 16,
            borderRadius: 8,
            backgroundColor: "#0070f3",
            color: "#fff",
            border: "none",
            cursor: "pointer",
          }}
          disabled={files.length === 0}
        >
          {uploading
            ? "Uploading..." // 👈 Show status
            : `Upload${files.length > 0 ? ` (${files.length})` : ""}`}
        </button>

        {uploading && (
          <div style={{ textAlign: "center", marginTop: 10, color: "#555" }}>
            ⏳ Please wait, processing your documents...
          </div>
        )}
      </div>
    </div>
  );
}
