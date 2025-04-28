// src/pages/DcaTracker.jsx

import React from "react";
import { motion } from "framer-motion";
import { Card } from "../components/ui/Card";

const dcaTrades = [
  {
    symbol: "USDT_XRP",
    step: 2,
    toBe: -3.5,
    health: "Healthy",
    confidence: 0.83,
    recoveryOdds: 0.85,
    spent: 125,
    budget: 200,
    risk: "low",
  },
  {
    symbol: "USDT_SHIB",
    step: 5,
    toBe: -6.8,
    health: "Weak",
    confidence: 0.62,
    recoveryOdds: 0.60,
    spent: 500,
    budget: 800,
    risk: "medium",
  },
  {
    symbol: "USDT_PAXG",
    step: 3,
    toBe: -10.5,
    health: "Zombie",
    confidence: 0.45,
    recoveryOdds: 0.40,
    spent: 1000,
    budget: 1000,
    risk: "high",
  },
];

const riskGlowMap = {
  low: "hover:shadow-[0_0_20px_4px_rgba(34,197,94,0.4)]",      // Green glow
  medium: "hover:shadow-[0_0_20px_4px_rgba(234,179,8,0.4)]",   // Yellow glow
  high: "hover:shadow-[0_0_20px_4px_rgba(239,68,68,0.4)]",     // Red glow
};

export default function DcaTracker() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-8 flex items-center gap-2">
        📈 DCA Tracker
      </h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dcaTrades.map((trade, idx) => (
          <motion.div
            key={idx}
            whileHover={{ scale: 1.03 }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
            className={`rounded-2xl p-6 bg-gradient-to-br from-black/10 to-black/20 ${riskGlowMap[trade.risk]} transition-all`}
          >
            <div className="text-xl font-bold mb-4">{trade.symbol}</div>

            <div className="text-sm mb-2">
              <strong>To BE:</strong> {trade.toBe}%
            </div>
            <div className="text-sm mb-2">
              <strong>Health:</strong> {trade.health}
            </div>
            <div className="text-sm mb-2">
              <strong>Conf:</strong> {trade.confidence}
            </div>
            <div className="text-sm mb-2">
              <strong>Odds:</strong> {trade.recoveryOdds}
            </div>

            <div className="mt-4">
              <div className="w-full bg-gray-800 rounded-full h-2 mb-2">
                <div
                  className="bg-green-400 h-2 rounded-full"
                  style={{ width: `${(trade.spent / trade.budget) * 100}%` }}
                ></div>
              </div>
              <div className="text-xs text-center text-muted-foreground">
                ${trade.spent} / ${trade.budget} spent
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
