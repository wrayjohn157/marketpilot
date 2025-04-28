// src/components/ui/DcaTradeFilter.jsx

import React, { useState } from "react";
import { Input } from "./Input";  // ✅ Correct relative path
import { Button } from "./Button";  // ✅ Correct relative path
import { Select, SelectTrigger, SelectContent, SelectItem } from "./Select";  // ✅ Correct relative path

export default function DcaTradeFilter({ onFilterChange }) {
  const [symbol, setSymbol] = useState("");
  const [sortBy, setSortBy] = useState("newest");

  const handleSymbolChange = (e) => {
    setSymbol(e.target.value);
    onFilterChange({ symbol: e.target.value, sortBy });
  };

  const handleSortChange = (value) => {
    setSortBy(value);
    onFilterChange({ symbol, sortBy: value });
  };

  return (
    <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4 mb-4">
      <Input
        placeholder="Filter by Symbol (e.g. DOGE)"
        value={symbol}
        onChange={handleSymbolChange}
        className="w-full md:w-64"
      />

      <Select value={sortBy} onValueChange={handleSortChange}>
        <SelectTrigger className="w-full md:w-52">
          Sort By: {sortBy === "newest" ? "Newest First" : sortBy === "pnl" ? "PnL %" : sortBy === "dca" ? "DCA Steps" : "Drawdown"}
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="newest">Newest First</SelectItem>
          <SelectItem value="pnl">PnL %</SelectItem>
          <SelectItem value="drawdown">Drawdown %</SelectItem>
          <SelectItem value="dca">DCA Steps</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
