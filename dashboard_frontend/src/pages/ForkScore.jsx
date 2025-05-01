import React from "react";
import ForkScoreConfigPanel from "../components/ConfigPanels/ForkScoreConfigPanel";

export default function ForkScore() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">⚙️ Fork Score Config</h1>
      <ForkScoreConfigPanel />
    </div>
  );
}
