"use client";
import { useState, useEffect } from "react";
import axios from "axios";

export default function Home() {
  const [file, setFile] = useState(null);
  const [uploaded, setUploaded] = useState(false);
  const [chat, setChat] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");

  // Create session on page load
  useEffect(() => {
    const createSession = async () => {
      try {
        const res = await axios.post("http://localhost:8000/session");
        setSessionId(res.data.session_id);
        console.log("Session created:", res.data.session_id);
      } catch (err) {
        console.error("Error creating session:", err);
      }
    };
    createSession();
  }, []);

  // Upload the file
  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first!");
      return;
    }
    if (!sessionId) {
      alert("Session not initialized yet.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionId);

    try {
      const res = await axios.post("http://localhost:8000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      if (res.data.success) {
        setUploaded(true);
        alert(res.data.message);
      }
    } catch (err) {
      console.error(err);
      alert("Error uploading file.");
    }
  };

  // Send a question to backend
  const sendQuestion = async () => {
    if (!input.trim()) return;
    if (!sessionId) {
      alert("Session not initialized yet.");
      return;
    }

    setLoading(true);

    try {
      const res = await axios.post("http://localhost:8000/ask", {
        session_id: sessionId,
        question: input,
      });
      setChat((prev) => [...prev, { question: input, answer: res.data.answer }]);
      setInput("");
    } catch (err) {
      console.error(err);
      alert("Error connecting to backend");
    }

    setLoading(false);
  };

  // Clear session
  const clearSession = async () => {
    if (!sessionId) return;
    try {
      await axios.post("http://localhost:8000/clear_session", null, {
        params: { session_id: sessionId },
      });
      setChat([]);
      setUploaded(false);
      setFile(null);
      alert("Session cleared and vectors deleted!");
    } catch (err) {
      console.error(err);
      alert("Error clearing session.");
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "50px auto", fontFamily: "Inter, Arial, sans-serif", display: "flex", flexDirection: "column", height: "80vh" }}>
      <h1 style={{ textAlign: "center", marginBottom: 20 }}>
        <img src="/uploadit.png" alt="UploadiT Logo" style={{ height: 50, verticalAlign: "middle" }} />
        UploadiT
      </h1>

      {!uploaded ? (
        <div style={{ border: "2px dashed #0070f3", borderRadius: 10, padding: 40, textAlign: "center" }}>
          <input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setFile(e.target.files[0])} style={{ marginBottom: 20 }} />
          <br />
          <button onClick={handleUpload} style={{ padding: "12px 20px", fontSize: 16, borderRadius: 8, backgroundColor: "#0070f3", color: "#fff", border: "none", cursor: "pointer" }}>
            Upload
          </button>
        </div>
      ) : (
        <>
          <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 15, flexGrow: 1, overflowY: "auto", backgroundColor: "#fafafa", boxShadow: "0 4px 10px rgba(0,0,0,0.05)" }}>
            {chat.map((item, idx) => (
              <div key={idx} style={{ marginBottom: 20 }}>
                <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8 }}>
                  <div style={{ background: "#0070f3", color: "#fff", padding: "10px 15px", borderRadius: "18px 18px 4px 18px", maxWidth: "70%", fontSize: "15px", lineHeight: "1.5", wordBreak: "break-word" }}>
                    {item.question}
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-start" }}>
                  <div style={{ background: "#e9e9eb", color: "#222", padding: "10px 15px", borderRadius: "18px 18px 18px 4px", maxWidth: "70%", fontSize: "15px", lineHeight: "1.5", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                    {item.answer}
                  </div>
                </div>
              </div>
            ))}

            {loading && <div style={{ textAlign: "left", color: "#555", fontStyle: "italic", marginTop: 10 }}>Bot is typing...</div>}
          </div>

          <div style={{ display: "flex", marginTop: 15 }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              style={{ flex: 1, padding: "12px 15px", fontSize: 16, borderRadius: 8, border: "1px solid #ccc", outline: "none" }}
              placeholder="Ask a question..."
              onKeyDown={(e) => e.key === "Enter" && sendQuestion()}
            />
            <button onClick={sendQuestion} style={{ marginLeft: 10, padding: "12px 20px", fontSize: 16, borderRadius: 8, backgroundColor: "#0070f3", color: "#fff", border: "none", cursor: "pointer" }}>
              Ask
            </button>
            <button onClick={clearSession} style={{ marginLeft: 10, padding: "12px 20px", fontSize: 16, borderRadius: 8, backgroundColor: "#f44336", color: "#fff", border: "none", cursor: "pointer" }}>
              Clear Session
            </button>
          </div>
        </>
      )}
    </div>
  );
}
