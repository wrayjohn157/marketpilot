// src/components/DcaTradeCard.jsx

import React, { useState } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "./ui/Button";
import { Card, CardContent } from "./ui/Card";
import { Sparkline } from "./ui/Sparkline";
import { PriceProgressBar } from "./ui/PriceProgressBar";

export default function DcaTradeCard({ trade }) {
  const [liveTrade, setLiveTrade] = useState(trade);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const {
    deal_id,
    symbol,
    avg_entry_price,
    current_price,
    tp1_shift,
    be_price,
    step,
    open_pnl,
    confidence_score,
    recovery_odds,
    safu_score,
    entry_score,
    current_score,
    sparkline_data = [],
  } = liveTrade;

  // Parse numbers
  const entry = parseFloat(avg_entry_price) || 1;
  const current = parseFloat(current_price) || entry;
  const breakEven = parseFloat(be_price) || entry;
  const tp1 = breakEven * (1 + (parseFloat(tp1_shift) || 0) / 100);

  const refreshPrice = async () => {
    setIsRefreshing(true);
    try {
      const res = await fetch(`/refresh-price/${deal_id}`);
      const data = await res.json();

      if (data?.current_price) {
        setLiveTrade(prev => ({
          ...prev,
          current_price: data.current_price,
          open_pnl: data.open_pnl ?? prev.open_pnl,
          pnl_pct: data.pnl_pct ?? prev.pnl_pct,
        }));
      } else {
        console.error("⚠️ Invalid refresh payload:", data);
      }
    } catch (e) {
      console.error("❌ Network error during refresh:", e);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <Card className="relative flex flex-col md:flex-row rounded-2xl shadow-md overflow-hidden bg-gray-900 dark:bg-gray-900">
      {/* ── LEFT: Sparkline ───────────────────────────── */}
      {sparkline_data.length > 1 && (
        <div className="md:w-1/3 h-36 p-2 relative overflow-hidden">
          <Sparkline data={sparkline_data} />
        </div>
      )}

      {/* ── RIGHT: Main Content ───────────────────────────── */}
      <div className="flex-1 p-4 flex flex-col justify-between space-y-4">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold">{symbol}</h2>
          <Button size="sm" onClick={refreshPrice} disabled={isRefreshing}>
            {isRefreshing
              ? <RefreshCw className="w-4 h-4 animate-spin" />
              : "Refresh"}
          </Button>
        </div>

        {/* Live PnL Bar */}
        <div>
          <PriceProgressBar current={current} breakEven={breakEven} tp1={tp1} />
          <div className="mt-1 flex justify-between text-xs text-muted-foreground">
            <span>Entry: {entry.toFixed(4)}</span>
            <span>TP1: {tp1.toFixed(4)}</span>
          </div>
        </div>

        {/* Stats Grid */}
        <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-4 text-xs text-muted-foreground">
          <div>
            <div className="font-medium">Step</div>
            <div>{step}</div>
          </div>
          <div>
            <div className="font-medium">PnL</div>
            <div className={open_pnl < 0 ? "text-red-400" : "text-green-400"}>
              {(open_pnl ?? 0).toFixed(2)} USDT
            </div>
          </div>
          <div>
            <div className="font-medium">Conf</div>
            <div>{confidence_score?.toFixed(2)}</div>
          </div>
          <div>
            <div className="font-medium">Odds</div>
            <div>{recovery_odds?.toFixed(2)}</div>
          </div>
          <div>
            <div className="font-medium">SAFU</div>
            <div>{safu_score?.toFixed(2)}</div>
          </div>
          <div>
            <div className="font-medium">Score</div>
            <div>
              {entry_score?.toFixed(2)} → {current_score?.toFixed(2)}
            </div>
          </div>
        </CardContent>
      </div>
    </Card>
  );
}
