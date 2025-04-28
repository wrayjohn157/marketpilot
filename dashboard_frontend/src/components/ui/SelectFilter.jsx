// src/components/ui/SelectFilter.jsx
import React from "react";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem
} from "./Select";

export default function SelectFilter({ label, options = [], value, onChange }) {
  return (
    <div className="text-sm text-white space-y-1">
      <label className="text-muted-foreground">{label}</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full bg-muted border border-gray-600 rounded-md text-white">
          <SelectValue placeholder={`Select ${label}`} />
        </SelectTrigger>
        <SelectContent className="bg-black border border-gray-700 text-white">
          {options.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
