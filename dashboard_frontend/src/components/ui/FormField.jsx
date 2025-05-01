// src/components/ui/FormField.jsx
import React from "react";

export function FormField({ label, className = "", children }) {
  return (
    <div
      className={
        "grid grid-cols-[8rem,1fr] sm:grid-cols-[10rem,1fr] items-center gap-x-4 gap-y-2 " +
        className
      }
    >
      <label className="text-sm text-gray-300">{label}</label>
      {children}
    </div>
  );
}
