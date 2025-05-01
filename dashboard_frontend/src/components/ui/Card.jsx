// src/components/ui/Card.jsx
import React from "react";

export function Card({ children, className = "", ...props }) {
  return (
    <div className={`rounded-lg bg-muted p-4 shadow-md ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className = "", ...props }) {
  return (
    <div className={`mb-2 border-b border-gray-700 pb-2 ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = "", ...props }) {
  return (
    <h2 className={`text-lg font-semibold text-white ${className}`} {...props}>
      {children}
    </h2>
  );
}

export function CardContent({ children, className = "", ...props }) {
  return (
    <div className={`p-2 ${className}`} {...props}>
      {children}
    </div>
  );
}
