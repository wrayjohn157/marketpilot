import React from "react";
import DcaConfigPanel from "../components/ConfigPanels/DcaConfigPanel";

export default function DcaConfig() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">⚙️ DCA Config</h1>
      <DcaConfigPanel />
    </div>
  );
}
