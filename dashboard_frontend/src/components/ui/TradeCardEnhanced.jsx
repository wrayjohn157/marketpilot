import React, { useState, useEffect } from "react";
import { RefreshCw, ShieldCheck, TrendingUp, Activity, Percent, Zap } from "lucide-react";
import { Button } from "./Button";
import { Card } from "./Card";
import { Sparkline } from "./Sparkline";
import { TradingViewChart } from "./TradingViewChart";

export default function TradeCard({ trade }) {
  const [liveTrade, setLiveTrade] = useState(trade);
  const [loading, setLoading] = useState(false);
  const [confirmClose, setConfirmClose] = useState(false);
  const [showChart, setShowChart] = useState(false);

  const {
    deal_id,
    symbol,
    avg_entry_price,
    current_price,
    tp1_shift,
    entry_score,
    current_score,
    confidence_score,
    recovery_odds,
    safu_score,
    step,
    open_pnl,
    pnl_pct,
    sparkline_data = [],
    rejection_reason,
    be_price,
  } = liveTrade;

  const entry = parseFloat(avg_entry_price) || 1;
  const current = parseFloat(current_price) || entry;
  const breakEven = parseFloat(be_price) || entry;
  const tp1 = breakEven * (1 + (parseFloat(tp1_shift) || 0) / 100);

  const [isMobile, setIsMobile] = useState(window.innerWidth < 640);
  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 640);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    const fetchDcaEval = async () => {
      try {
        const res = await fetch("/dca-evals");
        const json = await res.json();
        const data = Array.isArray(json) ? json : json.evaluations;

        if (Array.isArray(data)) {
          const match = data.find(d => d.deal_id === deal_id);
          if (match) {
            setLiveTrade(prev => ({
              ...prev,
              ...match,
            }));
          }
        } else {
          console.error("❌ DCA evals response is not an array:", json);
        }
      } catch (err) {
        console.error("❌ Error fetching DCA evals:", err);
      }
    };

    fetchDcaEval();
  }, [deal_id]);

  const refreshPrice = async () => {
    setLoading(true);
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
      console.error("❌ Refresh error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleForceClose = async (deal_id, pair) => {
    try {
      const res = await fetch("/panic-sell", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ deal_id }),
      });

      if (res.ok) {
        const data = await res.json();
        alert(
          `🚨 Panic Sell Complete\n\n${pair}\nClosed at ${data.close_price?.toFixed(4)} for ${
            data.pnl_pct?.toFixed(2)
          }%\n→ ${data.pnl_usdt?.toFixed(2)} USDT\nStatus: ${data.status || "n/a"}`
        );
        window.location.reload();
      } else {
        alert("❌ Panic sell request failed");
      }
    } catch (e) {
      console.error("❌ Panic sell error:", e);
      alert("❌ Panic sell failed or display error — please check console.");
    }
  };

  return (
    <>
      {/* Sparkline ghost background */}
      {sparkline_data.length > 1 && (
        <div className="absolute inset-0 opacity-5 blur-[3px] pointer-events-none">
          <Sparkline data={sparkline_data} />
        </div>
      )}

      {/* Main Card content */}
      <Card className="w-full max-w-md border border-gray-800 ring-1 ring-gray-700 rounded-xl p-4 shadow-md bg-gray-900/80 backdrop-blur-sm">
        {/* Top: Symbol and Refresh */}
        <div className="flex justify-between items-center mb-2">
          <button
            onClick={() => setShowChart(true)}
            className="text-base font-semibold tracking-tight text-white hover:underline"
            title="View on TradingView"
          >
            {symbol}
          </button>
          <Button size="xs" variant="ghost" onClick={refreshPrice} disabled={loading} title="Refresh">
            <RefreshCw className="w-4 h-4 text-green-400" />
          </Button>
        </div>
        {/* Entry/TP1 & Reason */}
        <div className="text-sm text-muted-foreground">
          Entry: {entry.toFixed(4)} › TP1: {tp1.toFixed(4)}
        </div>
        {rejection_reason && (
          <div className="italic text-yellow-400 text-xs mt-1">
            Reason: {rejection_reason.replaceAll("_", " ").toUpperCase()}
          </div>
        )}
        {/* Stats grid */}
        <div className="grid grid-cols-3 gap-3 text-xs text-muted-foreground mt-3">
          <div>
            <div className="text-[10px] uppercase">Score</div>
            <div className="text-white font-medium">{entry_score?.toFixed(2)} → {current_score?.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase">SAFU</div>
            <div className="text-white font-medium">{safu_score?.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase">Conf</div>
            <div className="text-white font-medium">{confidence_score?.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase">Odds</div>
            <div className="text-white font-medium">{recovery_odds?.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase">Step</div>
            <div className="text-white font-medium">{step ?? 0}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase">PnL</div>
            <div className={open_pnl >= 0 ? "text-green-400 font-semibold" : "text-red-400 font-semibold"}>
              {(typeof open_pnl === "number" ? open_pnl.toFixed(2) : "N/A")} USDT <span className="text-muted">({pnl_pct?.toFixed(2)}%)</span>
            </div>
          </div>
        </div>
        {/* Enhanced progress bar: symmetrical with BE as center */}
        <div className="relative w-full h-4 rounded-full bg-gray-800 overflow-hidden mt-4 mb-2 border border-gray-700">
          {/* Red zone fill (left of BE) */}
          {current < breakEven && (
            <div
              className="absolute top-0 bottom-0 left-0 bg-red-500"
              style={{
                width: `${((current - Math.min(entry, breakEven)) / (breakEven - Math.min(entry, breakEven))) * 50}%`
              }}
              title={`Now: $${current.toFixed(4)}`}
            />
          )}

          {/* Green zone fill (right of BE) */}
          {current >= breakEven && (
            <div
              className="absolute top-0 bottom-0 left-1/2 bg-green-500"
              style={{
                width: `${((Math.min(current, tp1) - breakEven) / (tp1 - breakEven)) * 50}%`
              }}
              title={`Now: $${current.toFixed(4)}`}
            />
          )}

          {/* Break-even marker */}
          <div className="absolute top-0 bottom-0 w-[2px] bg-yellow-400 left-1/2" title="Break Even" />

          {/* Entry marker */}
          <div
            className="absolute top-0 bottom-0 w-[2px] bg-white/70"
            style={{
              left: `${((entry - Math.min(entry, tp1)) / (tp1 - Math.min(entry, tp1))) * 100}%`
            }}
            title="Entry"
          />

          {/* TP1 marker */}
          <div
            className="absolute top-0 bottom-0 w-[2px] bg-blue-400"
            style={{ left: "100%" }}
            title="TP1"
          />
        </div>
        <div className="flex justify-between text-[10px] text-muted-foreground -mt-1">
          <span>${Math.min(entry, tp1).toFixed(4)}</span>
          <span>BE: ${breakEven.toFixed(4)}</span>
          <span>${tp1.toFixed(4)}</span>
        </div>
        {/* Tag row */}
        <div className="flex justify-start gap-4 text-xs text-white mt-2">
          {liveTrade.is_zombie ? (
            <div className="flex items-center gap-1 text-red-400">
              <Activity className="w-4 h-4" /> Zombie
            </div>
          ) : (
            <>
              {safu_score >= 0.5 && recovery_odds >= 0.75 && confidence_score >= 0.7 && (
                <>
                  <div className="flex items-center gap-1 text-green-400">
                    <ShieldCheck className="w-4 h-4" /> SAFU
                  </div>
                  <div className="flex items-center gap-1 text-yellow-400">
                    <Zap className="w-4 h-4" /> Recovery Odds
                  </div>
                </>
              )}
              {!(safu_score >= 0.5 && recovery_odds >= 0.75 && confidence_score >= 0.7) && (
                <div className="text-gray-500 italic text-xs">No qualifying tags</div>
              )}
            </>
          )}
        </div>
        {/* Sparkline is background only */}
        {/* Always-on Panic Sell button with confirmation */}
        <div className="mt-4 flex justify-end">
          <button
            className="border border-red-500 text-red-500 px-3 py-1 rounded hover:bg-red-100"
            onClick={() => {
              const confirmClose = window.confirm("⚠️ Are you sure you want to panic sell this trade?");
              if (confirmClose) {
                handleForceClose(deal_id, symbol);
              }
            }}
          >
            ⚠️ Panic Sell
          </button>
        </div>
      </Card>
      {showChart && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-4 w-full max-w-4xl relative">
            <button
              onClick={() => setShowChart(false)}
              className="absolute top-2 right-2 text-black hover:text-red-500 text-xl font-bold"
            >
              ×
            </button>
            <TradingViewChart symbol={symbol} interval="1h" />
          </div>
        </div>
      )}
    </>
  );
}
