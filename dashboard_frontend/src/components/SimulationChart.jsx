import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';

// Chart component for DCA simulation visualization
const SimulationChart = ({
  data = [],
  dcaPoints = [],
  entryPoint = null,
  height = 400,
  width = '100%',
  onCandleClick = null,
  selectedCandle = null
}) => {
  const canvasRef = useRef(null);
  const [chartData, setChartData] = useState(null);
  const [hoveredCandle, setHoveredCandle] = useState(null);

  // Process data for chart rendering
  useEffect(() => {
    if (data && data.length > 0) {
      const processedData = data.map(candle => ({
        timestamp: new Date(candle.timestamp),
        open: parseFloat(candle.open),
        high: parseFloat(candle.high),
        low: parseFloat(candle.low),
        close: parseFloat(candle.close),
        volume: parseFloat(candle.volume)
      }));
      setChartData(processedData);
    }
  }, [data]);

  // Draw chart
  useEffect(() => {
    if (!chartData || chartData.length === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Chart dimensions
    const padding = 40;
    const chartWidth = rect.width - padding * 2;
    const chartHeight = rect.height - padding * 2;

    // Find price range
    const prices = chartData.flatMap(candle => [candle.high, candle.low]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice;
    const pricePadding = priceRange * 0.1;

    // Price scale
    const priceScale = (price) =>
      chartHeight - ((price - (minPrice - pricePadding)) / (priceRange + pricePadding * 2)) * chartHeight;

    // Time scale
    const timeScale = (index) => (index / (chartData.length - 1)) * chartWidth;

    // Draw grid
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padding + (i / 5) * chartHeight;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(padding + chartWidth, y);
      ctx.stroke();
    }

    // Draw candlesticks
    chartData.forEach((candle, index) => {
      const x = padding + timeScale(index);
      const openY = padding + priceScale(candle.open);
      const closeY = padding + priceScale(candle.close);
      const highY = padding + priceScale(candle.high);
      const lowY = padding + priceScale(candle.low);

      // Determine candle color
      const isGreen = candle.close >= candle.open;
      ctx.strokeStyle = isGreen ? '#10b981' : '#ef4444';
      ctx.fillStyle = isGreen ? '#10b981' : '#ef4444';

      // Draw wick
      ctx.beginPath();
      ctx.moveTo(x, highY);
      ctx.lineTo(x, lowY);
      ctx.stroke();

      // Draw body
      const bodyHeight = Math.abs(closeY - openY);
      const bodyY = Math.min(openY, closeY);

      if (bodyHeight > 0) {
        ctx.fillRect(x - 2, bodyY, 4, bodyHeight);
      } else {
        // Doji
        ctx.beginPath();
        ctx.moveTo(x - 2, openY);
        ctx.lineTo(x + 2, openY);
        ctx.stroke();
      }
    });

    // Draw DCA points
    dcaPoints.forEach(point => {
      const pointTime = new Date(point.timestamp);
      const pointIndex = chartData.findIndex(candle =>
        Math.abs(candle.timestamp - pointTime) < 1000 * 60 * 60 // Within 1 hour
      );

      if (pointIndex >= 0) {
        const x = padding + timeScale(pointIndex);
        const y = padding + priceScale(point.price);

        // DCA point circle
        ctx.fillStyle = '#ff6b6b';
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, 2 * Math.PI);
        ctx.fill();

        // DCA point border
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();

        // DCA point label
        ctx.fillStyle = '#ffffff';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(`DCA ${point.dca_count}`, x, y - 10);
      }
    });

    // Draw entry point
    if (entryPoint) {
      const entryTime = new Date(entryPoint.timestamp);
      const entryIndex = chartData.findIndex(candle =>
        Math.abs(candle.timestamp - entryTime) < 1000 * 60 * 60
      );

      if (entryIndex >= 0) {
        const x = padding + timeScale(entryIndex);
        const y = padding + priceScale(entryPoint.price);

        // Entry point triangle
        ctx.fillStyle = '#4ecdc4';
        ctx.beginPath();
        ctx.moveTo(x, y - 8);
        ctx.lineTo(x - 6, y + 4);
        ctx.lineTo(x + 6, y + 4);
        ctx.closePath();
        ctx.fill();

        // Entry point label
        ctx.fillStyle = '#ffffff';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('ENTRY', x, y - 12);
      }
    }

    // Draw price labels
    ctx.fillStyle = '#9ca3af';
    ctx.font = '12px Arial';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
      const price = minPrice - pricePadding + (i / 5) * (priceRange + pricePadding * 2);
      const y = padding + (i / 5) * chartHeight;
      ctx.fillText(price.toFixed(2), padding - 10, y + 4);
    }

    // Draw time labels
    ctx.textAlign = 'center';
    const timeStep = Math.max(1, Math.floor(chartData.length / 5));
    for (let i = 0; i < chartData.length; i += timeStep) {
      const x = padding + timeScale(i);
      const time = chartData[i].timestamp.toLocaleTimeString();
      ctx.fillText(time, x, chartHeight + padding + 20);
    }

  }, [chartData, dcaPoints, entryPoint, height, width]);

  // Handle canvas click
  const handleCanvasClick = (event) => {
    if (!onCandleClick || !chartData) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const padding = 40;
    const chartWidth = rect.width - padding * 2;
    const chartHeight = rect.height - padding * 2;

    // Find clicked candle
    const candleIndex = Math.round(((x - padding) / chartWidth) * (chartData.length - 1));
    const candle = chartData[candleIndex];

    if (candle) {
      onCandleClick(candle, candleIndex);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>DCA Simulation Chart</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <canvas
            ref={canvasRef}
            width={width}
            height={height}
            onClick={handleCanvasClick}
            className="w-full border border-gray-700 rounded cursor-crosshair"
            style={{ width: '100%', height: `${height}px` }}
          />

          {/* Chart overlay for hover effects */}
          {hoveredCandle && (
            <div className="absolute top-4 left-4 bg-gray-800 text-white p-2 rounded text-sm">
              <div>Time: {hoveredCandle.timestamp.toLocaleString()}</div>
              <div>Open: {hoveredCandle.open.toFixed(2)}</div>
              <div>High: {hoveredCandle.high.toFixed(2)}</div>
              <div>Low: {hoveredCandle.low.toFixed(2)}</div>
              <div>Close: {hoveredCandle.close.toFixed(2)}</div>
              <div>Volume: {hoveredCandle.volume.toFixed(0)}</div>
            </div>
          )}
        </div>

        {/* Chart legend */}
        <div className="flex items-center justify-center mt-4 space-x-6 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>Bullish Candle</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span>Bearish Candle</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>DCA Point</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-0 h-0 border-l-4 border-r-4 border-b-6 border-l-transparent border-r-transparent border-b-cyan-400"></div>
            <span>Entry Point</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SimulationChart;
