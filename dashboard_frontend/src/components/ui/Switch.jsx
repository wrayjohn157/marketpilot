// src/components/ui/Switch.jsx
import React from "react";

export function Switch({ checked, onCheckedChange }) {
  return (
    <label className="flex items-center cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onCheckedChange(e.target.checked)}
        className="sr-only"
      />
      <div
        className={`w-10 h-5 flex items-center bg-gray-600 rounded-full p-1 transition-colors ${
          checked ? "bg-green-500" : "bg-gray-600"
        }`}
      >
        <div
          className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </div>
    </label>
  );
}
