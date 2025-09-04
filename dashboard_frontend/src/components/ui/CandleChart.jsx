import React, { useEffect, useRef, useState } from "react";

const CandleChart = ({ data, width: propWidth, height: propHeight, onCandleClick, dcaMarkers = [] }) => {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 });
  const [selectedIndex, setSelectedIndex] = useState(null);

  useEffect(() => {
    if (propWidth && propHeight) {
      setDimensions({ width: propWidth, height: propHeight });
    } else if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth || 600,
        height: containerRef.current.offsetHeight || 400,
      });
    }
  }, [propWidth, propHeight]);

  if (!data?.length) {
    return (
      <div
        ref={containerRef}
        className="w-full h-96 bg-gray-900 rounded-lg flex items-center justify-center text-gray-400"
        style={{ width: dimensions.width, height: dimensions.height }}
      >
        No data available
      </div>
    );
  }

  // Simple chart implementation using SVG
  const maxPrice = Math.max(...data.map(d => d.high));
  const minPrice = Math.min(...data.map(d => d.low));
  const priceRange = maxPrice - minPrice;
  const padding = 20;
  const chartWidth = dimensions.width - (padding * 2);
  const chartHeight = dimensions.height - (padding * 2);

  const getX = (index) => (index / (data.length - 1)) * chartWidth + padding;
  const getY = (price) => chartHeight - ((price - minPrice) / priceRange) * chartHeight + padding;

  const handleCandleClick = (index) => {
    setSelectedIndex(index);
    if (onCandleClick) {
      onCandleClick(data[index], index);
    }
  };

  return (
    <div
      ref={containerRef}
      className="w-full bg-gray-900 rounded-lg relative"
      style={{ width: dimensions.width, height: dimensions.height }}
    >
      <svg width={dimensions.width} height={dimensions.height} className="absolute inset-0">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
          <line
            key={`grid-h-${i}`}
            x1={padding}
            y1={getY(minPrice + priceRange * ratio)}
            x2={chartWidth + padding}
            y2={getY(minPrice + priceRange * ratio)}
            stroke="#374151"
            strokeWidth={1}
          />
        ))}

        {/* Candlesticks */}
        {data.map((candle, index) => {
          const x = getX(index);
          const openY = getY(candle.open);
          const closeY = getY(candle.close);
          const highY = getY(candle.high);
          const lowY = getY(candle.low);
          const isGreen = candle.close > candle.open;
          const isSelected = selectedIndex === index;

          return (
            <g key={index}>
              {/* High-Low line */}
              <line
                x1={x}
                y1={highY}
                x2={x}
                y2={lowY}
                stroke={isGreen ? "#10b981" : "#ef4444"}
                strokeWidth={1}
              />

              {/* Open-Close body */}
              <rect
                x={x - 2}
                y={Math.min(openY, closeY)}
                width={4}
                height={Math.abs(closeY - openY) || 1}
                fill={isGreen ? "#10b981" : "#ef4444"}
                stroke={isSelected ? "#fbbf24" : "none"}
                strokeWidth={isSelected ? 2 : 0}
                onClick={() => handleCandleClick(index)}
                className="cursor-pointer"
              />
            </g>
          );
        })}

        {/* DCA Markers */}
        {dcaMarkers.map((marker, index) => {
          const markerIndex = data.findIndex(d => d.time === marker.time);
          if (markerIndex === -1) return null;

          const x = getX(markerIndex);
          const y = getY(marker.price);

          return (
            <circle
              key={`dca-${index}`}
              cx={x}
              cy={y}
              r={4}
              fill="#fbbf24"
              stroke="#f59e0b"
              strokeWidth={2}
            />
          );
        })}
      </svg>

      {/* Price labels */}
      <div className="absolute right-2 top-2 text-xs text-gray-400">
        <div>High: {maxPrice.toFixed(2)}</div>
        <div>Low: {minPrice.toFixed(2)}</div>
      </div>

      {/* Selected candle info */}
      {selectedIndex !== null && (
        <div className="absolute bottom-2 left-2 bg-gray-800 p-2 rounded text-xs text-gray-300">
          <div>Time: {new Date(data[selectedIndex].time).toLocaleString()}</div>
          <div>O: {data[selectedIndex].open.toFixed(2)}</div>
          <div>H: {data[selectedIndex].high.toFixed(2)}</div>
          <div>L: {data[selectedIndex].low.toFixed(2)}</div>
          <div>C: {data[selectedIndex].close.toFixed(2)}</div>
        </div>
      )}
    </div>
  );
};

export default CandleChart;
