import { useEffect, useState } from "react";
import CandleChart from "../ui/CandleChart";
import { Card } from "../ui/Card";
import { Input } from "../ui/Input";
import { Label } from "../ui/Label";

const defaultParams = {
  entryScore: 0.75,
  currentScore: 0.62,
  safuScore: 0.85,
  drawdown: -11.0,
  tp1Shift: 5.2,
  confidence: 0.70,
  recoveryOdds: 0.65,
  rsi: 42.0,
  macdHistogram: 0.003,
  macdLift: 0.01,
  rsiSlope: 1.5,
  adx: 24.5,
  zombieTag: 0, // 1 = tagged
};

export default function DcaDecisionDebugger(props) {
  const liveParams = props.params || defaultParams;
  const [params, setParams] = useState(liveParams);
  const [series, setSeries] = useState([]);
  const [symbol, setSymbol] = useState("ARB");
  const [interval, setInterval] = useState("15m");

  useEffect(() => {
    fetch(`/price-series?symbol=${symbol}&interval=${interval}`)
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched price-series response:", data);
        if (data && Array.isArray(data.series)) {
          const mapped = data.series.map((d) => ({
            ...d,
            date: new Date(d.timestamp),
          }));
          setSeries(mapped);
        } else {
          console.warn("No valid 'series' array found in response:", data);
          setSeries([]);
        }
      })
      .catch((err) => {
        console.error("Fetch failed:", err);
        setSeries([]);
      });
  }, [symbol, interval]);

  const updateParam = (key, value) => {
    setParams((prev) => ({ ...prev, [key]: parseFloat(value) }));
  };

  return (
    <Card className="p-4 mt-4">
      <h2 className="text-blue-400 text-sm mb-2">📍 DCA Strategy Builder</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4 items-start">
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label>Symbol</Label>
              <Input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
            </div>
            <div>
              <Label>Interval</Label>
              <Input value={interval} onChange={(e) => setInterval(e.target.value)} />
            </div>
          </div>

          <div>
            <Label>Entry Score</Label>
            <Input
              type="number"
              step="0.01"
              value={params.entryScore}
              onChange={(e) => updateParam("entryScore", e.target.value)}
            />
          </div>
          <div>
            <Label>Current Score</Label>
            <Input
              type="number"
              step="0.01"
              value={params.currentScore}
              onChange={(e) => updateParam("currentScore", e.target.value)}
            />
          </div>
          <div>
            <Label>SAFU Score</Label>
            <Input
              type="number"
              step="0.01"
              value={params.safuScore}
              onChange={(e) => updateParam("safuScore", e.target.value)}
            />
          </div>
          <div>
            <Label>Drawdown %</Label>
            <Input
              type="number"
              step="0.1"
              value={params.drawdown}
              onChange={(e) => updateParam("drawdown", e.target.value)}
            />
          </div>
          <div>
            <Label>TP1 Shift %</Label>
            <Input
              type="number"
              step="0.1"
              value={params.tp1Shift}
              onChange={(e) => updateParam("tp1Shift", e.target.value)}
            />
          </div>
          <div>
            <Label>Confidence</Label>
            <Input
              type="number"
              step="0.01"
              value={params.confidence}
              onChange={(e) => updateParam("confidence", e.target.value)}
            />
          </div>
          <div>
            <Label>Recovery Odds</Label>
            <Input
              type="number"
              step="0.01"
              value={params.recoveryOdds}
              onChange={(e) => updateParam("recoveryOdds", e.target.value)}
            />
          </div>
          <div>
            <Label>RSI</Label>
            <Input
              type="number"
              step="0.1"
              value={params.rsi}
              onChange={(e) => updateParam("rsi", e.target.value)}
            />
          </div>
          <div>
            <Label>MACD Histogram</Label>
            <Input
              type="number"
              step="0.001"
              value={params.macdHistogram}
              onChange={(e) => updateParam("macdHistogram", e.target.value)}
            />
          </div>
          <div>
            <Label>MACD Lift</Label>
            <Input
              type="number"
              step="0.001"
              value={params.macdLift}
              onChange={(e) => updateParam("macdLift", e.target.value)}
            />
          </div>
          <div>
            <Label>RSI Slope</Label>
            <Input
              type="number"
              step="0.1"
              value={params.rsiSlope}
              onChange={(e) => updateParam("rsiSlope", e.target.value)}
            />
          </div>
          <div>
            <Label>ADX</Label>
            <Input
              type="number"
              step="0.1"
              value={params.adx}
              onChange={(e) => updateParam("adx", e.target.value)}
            />
          </div>
          <div>
            <Label>Zombie Tag</Label>
            <Input
              type="number"
              step="1"
              value={params.zombieTag}
              onChange={(e) => updateParam("zombieTag", e.target.value)}
            />
          </div>
        </div>

        <div>
          <Label className="mb-2 block">Price Series</Label>
          { (props.series || series).length > 0 ? (
            <div className="h-64 w-full">
              <CandleChart
                series={props.series || series}
                height={256}
                width={400}
              />
            </div>
          ) : (
            <div className="text-sm text-gray-500">No candle data loaded.</div>
          )}
        </div>
      </div>
    </Card>
  );
}
