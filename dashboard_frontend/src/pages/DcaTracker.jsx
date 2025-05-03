// src/pages/DcaTracker.jsx

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

const glowMap = {
  Healthy: "hover:shadow-[0_0_20px_4px_rgba(34,197,94,0.4)]",    // Green
  Weak: "hover:shadow-[0_0_20px_4px_rgba(234,179,8,0.4)]",       // Yellow
  Zombie: "hover:shadow-[0_0_20px_4px_rgba(239,68,68,0.4)]"      // Red
};

export default function DcaTracker() {
  const [trades, setTrades] = useState([]);

  useEffect(() => {
    fetch("/dca-evals")
      .then(res => res.json())
      .then(data => setTrades(data.evaluations || []))
      .catch(err => console.error("Failed to load DCA evals:", err));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-8 flex items-center gap-2">
        📈 DCA Tracker
      </h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {trades.map((trade, idx) => {
          const spent = trade.spent || 0;
          const budget = 2000;  // Static budget cap unless dynamic later
          const pct = Math.min((spent / budget) * 100, 100);

          let barColor = "bg-green-400";
          if (pct > 75) barColor = "bg-red-500";
          else if (pct > 50) barColor = "bg-yellow-400";

          return (
            <motion.div
              key={idx}
              whileHover={{ scale: 1.03 }}
              transition={{ type: "spring", stiffness: 200, damping: 20 }}
              className={`rounded-2xl p-6 bg-gradient-to-br from-black/10 to-black/20 ${glowMap[trade.health_status] || ""} transition-all`}
            >
              <div className="text-xl font-bold mb-4">{trade.symbol}</div>

              <div className="text-sm mb-1"><strong>Step:</strong> {trade.step}</div>
              <div className="text-sm mb-1"><strong>Health:</strong> {trade.health_status}</div>
              <div className="text-sm mb-1"><strong>Conf:</strong> {trade.confidence_score?.toFixed(2)}</div>
              <div className="text-sm mb-1"><strong>Odds:</strong> {trade.recovery_odds?.toFixed(2)}</div>
              <div className="text-sm mb-1"><strong>SAFU:</strong> {trade.safu_score?.toFixed(2)}</div>
              <div className="text-sm mb-1"><strong>Score:</strong> {trade.entry_score?.toFixed(2)} → {trade.current_score?.toFixed(2)}</div>
              <div className="text-sm mb-1"><strong>TP1 Shift:</strong> {trade.tp1_shift?.toFixed(2)}%</div>
              <div className="text-sm mb-1"><strong>BE Gain:</strong> {trade.be_improvement?.toFixed(2)}%</div>

              {trade.rejection_reason && (
                <div className="text-sm text-red-400">
                  ⛔ Reason: {trade.rejection_reason.replace("_", " ")}
                </div>
              )}

              <div className="mt-4">
                <div className="w-full bg-gray-800 rounded-full h-2 mb-2">
                  <div
                    className={`${barColor} h-2 rounded-full`}
                    style={{ width: `${pct}%` }}
                  ></div>
                </div>
                <div className="text-xs text-center text-muted-foreground">
                  ${spent.toFixed(2)} / ${budget} spent
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
