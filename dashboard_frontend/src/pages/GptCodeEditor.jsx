import React, { useState, useEffect } from "react";

export default function GptCodeEditor() {
  const [filePath, setFilePath] = useState("");
  const [instruction, setInstruction] = useState("");
  const [writeBack, setWriteBack] = useState(true);
  const [response, setResponse] = useState(null);
  const [fileList, setFileList] = useState([]);

  useEffect(() => {
    fetch("/config/gpt/files")
      .then(res => res.json())
      .then(data => {
        const files = Array.isArray(data) ? data : data.files;
        if (Array.isArray(files)) {
          setFileList(files);
        } else {
          console.error("⚠️ Unexpected file list format:", data);
        }
      })
      .catch(err => console.error("❌ Failed to load file list", err));
  }, []);

  const handleSubmit = async () => {
    try {
      const res = await fetch("/config//gpt/code-edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_path: filePath,
          instruction,
          write_back: writeBack
        })
      });

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      console.error("❌ Error during fetch:", err);
      setResponse({ result: "error", detail: "Request failed or invalid JSON" });
    }
  };

  return (
    <div className="p-6 max-w-3xl">
      <h1 className="text-2xl font-bold mb-4">🛠️ GPT Code Editor</h1>

      <label className="block mb-2 font-semibold">📄 File Path</label>
      <select
        className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600 mb-4"
        value={filePath}
        onChange={e => setFilePath(e.target.value)}
      >
        <option value="">-- Choose a file --</option>
        {fileList.map(file => (
          <option key={file} value={file}>{file}</option>
        ))}
      </select>

      <label className="block mb-2 font-semibold">📝 Instruction</label>
      <textarea
        className="w-full p-3 rounded bg-gray-800 text-white border border-gray-600 mb-4"
        rows={4}
        placeholder="Describe what to do with the file..."
        value={instruction}
        onChange={e => setInstruction(e.target.value)}
      />

      <div className="flex items-center space-x-6 mb-4">
        <label className="inline-flex items-center">
          <input
            type="checkbox"
            checked={writeBack}
            onChange={() => setWriteBack(!writeBack)}
            className="mr-2"
          />
          💾 Write to File
        </label>

        <label className="inline-flex items-center">
          <input
            type="checkbox"
            checked={!writeBack}
            onChange={() => setWriteBack(!writeBack)}
            className="mr-2"
          />
          🔍 Review Only
        </label>
      </div>

      <button
        onClick={handleSubmit}
        className="block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
        disabled={!filePath || !instruction}
      >
        Submit
      </button>

      {response && (
        <div className="mt-6 p-4 rounded bg-gray-900 text-gray-200 border border-gray-700 whitespace-pre-wrap">
          <div className="font-semibold mb-2">Response: {response.result}</div>
          {response.modified_code || response.detail || "No output"}
        </div>
      )}
    </div>
  );
}
