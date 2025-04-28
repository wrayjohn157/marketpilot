import React from "react";

export function Card({ children, className = "", ...props }) {
  return (
    <div className={`rounded-lg bg-muted p-4 shadow-md ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardContent({ children, className = "", ...props }) {
  return (
    <div className={`p-2 ${className}`} {...props}>
      {children}
    </div>
  );
}
