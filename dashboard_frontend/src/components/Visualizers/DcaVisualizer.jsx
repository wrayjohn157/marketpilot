import { useEffect, useState } from "react";
import {
    Bar,
    BarChart,
    Cell,
    Line,
    LineChart,
    ReferenceArea,
    ReferenceDot,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from "recharts";
import { Card, CardContent } from "../ui/Card.jsx";

const generateMockTrade = (config) => {
  const {
    macd_histogram = 0,
    rsi = 50,
    adx = 20,
    drawdown_trigger_pct = 0.9,
    base_order_usdt = 200,
  } = config || {};

  const data = [];
  let price = 1.0;

  const momentumBias = macd_histogram * 0.02; // directional drift
  const rsiBias = (rsi - 50) * 0.0005;        // slope change from neutral 50
  const adxFactor = Math.max(adx / 50, 0.2);  // controls curve sharpness (0.2–2.0)

  for (let i = 0; i < 60; i++) {
    const noise = (Math.random() - 0.5) * 0.01 * adxFactor;
    const change = momentumBias + rsiBias + noise;
    price = Math.max(price + change, 0.1); // clamp to avoid negative
    data.push({ time: `T-${60 - i}`, price: parseFloat(price.toFixed(4)) });
  }

  const entryIndex = 30;
  const entryPrice = data[entryIndex].price;

  const dcaSteps = [1, 2, 4].map((mult, i) => ({
    index: entryIndex + (i + 1) * 5,
    label: `SO${i + 1}`,
    price: parseFloat((entryPrice * (1 - drawdown_trigger_pct * (i + 1))).toFixed(4)),
    volume: mult * base_order_usdt,
  }));

  return { data, entryIndex, entryPrice, dcaSteps };
};

export default function DcaVisualizer({ config = {}, btcStatus = "SAFE" }) {
  const [tradeSim, setTradeSim] = useState(() => generateMockTrade(config));

  useEffect(() => {
    setTradeSim(generateMockTrade(config));
  }, [config]);

  const { data, entryIndex, entryPrice, dcaSteps } = tradeSim;
  const entryTime = data[entryIndex].time;
  const tp1Pct = config.tp1_pct_target || 0.025;
  const tp1Low = entryPrice * (1 + tp1Pct * 0.95);
  const tp1High = entryPrice * (1 + tp1Pct * 1.05);

  const dcaLadder = [
    { step: "Base", amount: config.base_order_usdt || 200 },
    ...[1, 2, 4].map((m, i) => ({
      step: `SO${i + 1}`,
      amount: m * (config.base_order_usdt || 200),
    })),
  ];

  return (
    <Card className="mt-4">
      <CardContent>
        <h2 className="text-xl font-semibold mb-2">📈 DCA Visualizer</h2>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <XAxis dataKey="time" hide />
            <YAxis domain={["auto", "auto"]} />
            <Tooltip />

            {/* Price line */}
            <Line type="monotone" dataKey="price" stroke="#10b981" strokeWidth={2} dot={false} />

            {/* Entry dot */}
            <ReferenceDot x={entryTime} y={entryPrice} r={5} fill="green" label="Entry" />

            {/* BTC filter shading */}
            {config.use_btc_filter && btcStatus === "BEARISH" && (
              <ReferenceArea
                x1={data[entryIndex - 10]?.time}
                x2={data[entryIndex + 25]?.time}
                y1="auto"
                y2="auto"
                strokeOpacity={0.1}
                fill="gray"
                label="BTC Bearish"
              />
            )}

            {/* TP1 recovery zone */}
            <ReferenceArea
              y1={tp1Low}
              y2={tp1High}
              strokeOpacity={0.1}
              fill="#c084fc"
              label="TP1 Recovery Zone"
            />

            {/* DCA step dots */}
            {dcaSteps.map((step, idx) => (
              <ReferenceDot
                key={idx}
                x={data[step.index]?.time || data[data.length - 1].time}
                y={step.price}
                r={4}
                fill="red"
                label={`${step.label} $${step.volume}`}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>

        {/* DCA ladder chart */}
        <div className="mt-6">
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={dcaLadder}>
              <XAxis dataKey="step" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="amount">
                {dcaLadder.map((entry, index) => (
                  <Cell key={index} fill={index === 0 ? "#10b981" : "#ef4444"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-muted mt-1 text-center">USDT Allocation Per Step</p>
        </div>

        <p className="text-sm text-muted mt-2">
          Entry: ${entryPrice.toFixed(4)} | Base: ${config.base_order_usdt || 200} | BTC: {btcStatus}
        </p>
      </CardContent>
    </Card>
  );
}
