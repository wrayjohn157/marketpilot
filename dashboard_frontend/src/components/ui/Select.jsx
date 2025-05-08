import React from "react";

export function Select({ value, onValueChange, children }) {
  return (
    <select
      value={value}
      onChange={(e) => onValueChange(e.target.value)}
      className="bg-gray-900 text-white rounded p-2 w-full border border-gray-600"
    >
      {children}
    </select>
  );
}

export const SelectTrigger = ({ children }) => <>{children}</>;
export const SelectValue = ({ placeholder }) => <option disabled>{placeholder}</option>;

export const SelectContent = ({ children }) => <>{children}</>;
export const SelectItem = ({ children, value }) => (
  <option value={value}>{children}</option>
);
