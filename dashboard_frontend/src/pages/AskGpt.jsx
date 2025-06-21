// pages/AskGpt.jsx
import React, { useState } from "react";

export default function AskGpt() {
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const sendPrompt = async () => {
    setLoading(true);
    setResponse("");
    try {
      const res = await fetch("/gpt/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, use_context: true }),
      });
      const data = await res.json();
      setResponse(data.reply || "No reply");
    } catch (err) {
      setResponse("Error: " + err.message);
    }
    setLoading(false);
  };

  return (
    <div className="p-6 max-w-xl">
      <h1 className="text-2xl font-bold mb-4">🤖 Ask ChatGPT</h1>
      <textarea
        className="w-full p-3 rounded bg-gray-800 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows={4}
        placeholder="Ask a question about your trades, DCA logic, fork scores..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      <button
        onClick={sendPrompt}
        className="mt-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition disabled:opacity-50"
        disabled={loading || !prompt.trim()}
      >
        {loading ? "Thinking..." : "Ask GPT"}
      </button>
      {response && (
        <div className="mt-4 p-4 rounded bg-gray-900 text-gray-200 border border-gray-700 whitespace-pre-wrap">
          {response}
        </div>
      )}
    </div>
  );
}
