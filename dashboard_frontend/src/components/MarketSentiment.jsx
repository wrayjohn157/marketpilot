import React, { useEffect, useState } from "react";
import { Minus, Signal, MoveUpRight, Frown, Smile, Meh } from "lucide-react";
import apiClient from "../lib/api";

export default function MarketSentiment() {
  const [data, setData] = useState(null);

  useEffect(() => {
    apiClient.getBTCContext()
      .then((res) => {
        setData({
          status: res.status?.toUpperCase() || "UNKNOWN",
          rsi: parseFloat(res.rsi).toFixed(1),
          adx: parseFloat(res.adx).toFixed(1),
          emaRelation: res.close > res.ema ? "Above EMA50" : "Below EMA50",
          // dominance: res.dominance, // ← future use
        });
      })
      .catch((err) => {
        console.error("Failed to fetch BTC sentiment:", err);
        setData(null);
      });
  }, []);

  const statusColor =
    data?.status === "BULLISH"
      ? "text-green-400"
      : data?.status === "BEARISH"
      ? "text-red-400"
      : "text-yellow-400";

  const statusIcon =
    data?.status === "BULLISH" ? (
      <Smile className="w-6 h-6 text-green-400" />
    ) : data?.status === "BEARISH" ? (
      <Frown className="w-6 h-6 text-red-400" />
    ) : (
      <Meh className="w-6 h-6 text-yellow-400" />
    );

  return (
    <div
      className="relative bg-gray-900 rounded-2xl p-4 shadow-md overflow-hidden border border-white/20"
      style={{ minHeight: "160px" }}
    >
      {/* Background globe */}
      <img
        src="/img/world.svg"
        alt="World Map"
        className="absolute inset-0 opacity-10 object-cover w-full h-full pointer-events-none"
      />

      <div className="relative z-10 flex flex-col h-full justify-between">
        {/* Title + Sentiment */}
        <div className="mb-2">
          <h2 className="text-sm text-gray-300 font-medium mb-1">
            Market Sentiment & BTC Health
          </h2>
          <div className="flex items-center gap-3 text-lg font-bold">
            {statusIcon}
            <span className={`${statusColor} text-xl`}>
              {data?.status || "Loading..."}
            </span>
          </div>
        </div>

        {/* Indicators */}
        <div className="space-y-1 text-sm text-gray-200">
          <div className="flex items-center gap-2">
            <Minus className="w-4 h-4 text-gray-300" />
            <span>RSI: {data?.rsi || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <Signal className="w-4 h-4 text-gray-300" />
            <span>ADX: {data?.adx || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <MoveUpRight className="w-4 h-4 text-green-400" />
            <span>{data?.emaRelation || "—"}</span>
          </div>
          {/* <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-blue-300" />
            <span>Dominance: {data?.dominance || "—"}</span>
          </div> */}
        </div>
      </div>
    </div>
  );
}
