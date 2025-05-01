// src/components/ForkScoreConfigPanel.jsx
import React, { useEffect, useState } from "react";

export default function ForkScoreConfigPanel() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/config/fork_score/")
      .then((res) => res.json())
      .then((data) => {
        setConfig(data);
        setLoading(false);
      })
      .catch((err) => {
        setError("Failed to load config");
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Loading config...</p>;
  if (error) return <p className="text-red-500">{error}</p>;

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow">
      <pre className="text-sm text-green-300 overflow-x-auto whitespace-pre-wrap">
        {JSON.stringify(config, null, 2)}
      </pre>
    </div>
  );
}
