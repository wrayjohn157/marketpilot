

import React, { useEffect, useState } from "react";
import axios from "axios";
import CandleChart from "../components/CandleChart";

const DcaStrategyBuilder = () => {
  const [symbol, setSymbol] = useState("ARB");
  const [interval, setInterval] = useState("15m");
  const [priceSeries, setPriceSeries] = useState([]);
  const [params, setParams] = useState({
    entryScore: 0.75,
    currentScore: 0.62,
    safuScore: 0.85,
    drawdownPct: -11,
    tp1ShiftPct: 5.2,
    confidence: 0.7,
    odds: 0.65,
    rsi: 42,
    macdHistogram: 0.003,
    macdLift: 0.01,
    rsiSlope: 1.5,
    adx: 24.5,
    zombieTag: 0,
  });

  useEffect(() => {
    const fetchPriceSeries = async () => {
      try {
        const res = await axios.get("/price-series", {
          params: { symbol, interval },
        });
        if (res.data?.series) {
          setPriceSeries(res.data.series);
        }
      } catch (err) {
        console.error("Failed to load price series:", err);
      }
    };
    fetchPriceSeries();
  }, [symbol, interval]);

  const updateParam = (key, value) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="p-6 text-white">
      <h2 className="text-2xl font-semibold mb-4">📌 DCA Strategy Builder</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="flex flex-col">
          <label>Symbol</label>
          <input value={symbol} onChange={(e) => setSymbol(e.target.value)} className="bg-gray-800 p-2 rounded" />
        </div>
        <div className="flex flex-col">
          <label>Interval</label>
          <input value={interval} onChange={(e) => setInterval(e.target.value)} className="bg-gray-800 p-2 rounded" />
        </div>
        <div className="flex flex-col">
          <label>Price Series</label>
          <span className="text-sm text-gray-400">
            {priceSeries.length ? `${priceSeries.length} candles loaded` : "No candle data loaded."}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {Object.entries(params).map(([key, val]) => (
          <div key={key} className="flex flex-col">
            <label className="capitalize">{key.replace(/([A-Z])/g, " $1")}</label>
            <input
              type="number"
              value={val}
              step="0.01"
              onChange={(e) => updateParam(key, parseFloat(e.target.value))}
              className="bg-gray-800 p-2 rounded"
            />
          </div>
        ))}
      </div>

      <div>
        <CandleChart series={priceSeries} />
      </div>
    </div>
  );
};

export default DcaStrategyBuilder;
