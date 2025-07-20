import React from "react";

export function PriceProgressBar({ current, breakEven, tp1 }) {
  if (!breakEven || !tp1 || breakEven === tp1) return null;

  const min = Math.min(current, breakEven, tp1);
  const max = Math.max(current, breakEven, tp1);
  const range = max - min;

  // % positions
  const currentPct = ((current - min) / range) * 100;
  const bePct = ((breakEven - min) / range) * 100;
  const tp1Pct = ((tp1 - min) / range) * 100;

  const isUnderwater = current < breakEven;
  const isInProfit = current >= breakEven && current < tp1;
  const isAboveTP1 = current >= tp1;

  return (
    <div className="relative w-full h-8">
      {/* Track */}
      <div className="absolute inset-0 h-2 bg-gray-800 rounded-full overflow-hidden" />

      {/* 🔴 Red fill: current → BE (if underwater) */}
      {isUnderwater && (
        <div
          className="absolute top-0 h-2 bg-red-500 rounded-full transition-all duration-500"
          style={{
            left: `${currentPct}%`,
            width: `${bePct - currentPct}%`,
          }}
        />
      )}

      {/* 🟢 Green fill: BE → TP1 (if in profit zone) */}
      {isInProfit && (
        <div
          className="absolute top-0 h-2 bg-green-500 rounded-full transition-all duration-500"
          style={{
            left: `${bePct}%`,
            width: `${currentPct - bePct}%`,
          }}
        />
      )}

      {/* ✅ Full green + glow if above TP1 */}
      {isAboveTP1 && (
        <>
          <div
            className="absolute top-0 h-2 bg-green-500 rounded-full transition-all duration-500"
            style={{
              left: `${bePct}%`,
              width: `${tp1Pct - bePct}%`,
            }}
          />
          {/* Glow beyond TP1 */}
          <div
            className="absolute top-0 h-2 rounded-full bg-lime-400 animate-pulse shadow-[0_0_10px_2px_rgba(132,204,22,0.6)]"
            style={{
              left: `${tp1Pct}%`,
              width: `8px`,
              height: '100%',
              borderRadius: '9999px'
            }}
          />
        </>
      )}

      {/* 🏷️ Price tag */}
      <div
        className="absolute top-3 text-[10px] text-white bg-black/80 px-1 rounded transition-all duration-500"
        style={{ left: `${currentPct}%`, transform: "translateX(-50%)" }}
      >
        {current.toFixed(4)}
      </div>

      {/* 🧷 BE label */}
      <div
        className="absolute top-3 text-[9px] text-blue-400"
        style={{ left: `${bePct}%`, transform: "translateX(-50%)" }}
      >
        BE
      </div>

      {/* 🧷 TP1 label */}
      <div
        className="absolute top-3 text-[9px] text-green-400"
        style={{ left: `${tp1Pct}%`, transform: "translateX(-50%)" }}
      >
        TP1
      </div>
    </div>
  );
}
