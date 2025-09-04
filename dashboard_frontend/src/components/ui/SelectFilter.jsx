import React from "react";
import { ChevronDown } from "lucide-react";

export default function SelectFilter({ label, options, value, onChange, className = "" }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-300">
          {label}
        </label>
      )}
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="appearance-none bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 pr-8 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full"
        >
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              className="bg-gray-800 text-white"
            >
              {option.label}
            </option>
          ))}
        </select>
        <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
          <ChevronDown className="w-4 h-4 text-gray-400" />
        </div>
      </div>
    </div>
  );
}
