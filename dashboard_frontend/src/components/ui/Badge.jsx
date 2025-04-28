// src/components/ui/Badge.jsx

import React from "react";

export function Badge({ children, variant = "default" }) {
  const base = "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium transition-transform transform hover:scale-105 hover:shadow-md";
  const variants = {
    default: "bg-gray-700 text-white hover:shadow-gray-500/50",
    secondary: "bg-gray-600 text-gray-100 hover:shadow-gray-400/50",
    success: "bg-green-600 text-white hover:shadow-green-400/50",
    warning: "bg-yellow-500 text-black hover:shadow-yellow-300/50",
    danger: "bg-red-600 text-white hover:shadow-red-400/50",
  };

  return (
    <span className={`${base} ${variants[variant] || variants.default}`}>
      {children}
    </span>
  );
}
