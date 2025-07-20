import { createChart } from "lightweight-charts";
import { useEffect, useRef, useState } from "react";

const CandleChart = ({ data, width: propWidth, height: propHeight, onCandleClick, dcaMarkers = [] }) => {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 });
  const [selectedIndex, setSelectedIndex] = useState(null);
  const formattedMarkersRef = useRef([]);

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

  useEffect(() => {
    if (!containerRef.current || !data?.length) return;

    if (chartRef.current) {
      chartRef.current.remove();
    }

    const chart = createChart(containerRef.current, {
      width: dimensions.width,
      height: dimensions.height,
      layout: {
        background: { color: "#ffffff" },
        textColor: "#000000",
      },
      grid: {
        vertLines: { color: "#eee" },
        horzLines: { color: "#eee" },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: "#ccc",
      },
      timeScale: {
        borderColor: "#ccc",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candlestickSeries = chart.addCandlestickSeries();
    chartRef.current = chart;
    seriesRef.current = candlestickSeries;

    const formatted = data.map((d) => ({
      time: Math.floor(d.timestamp / 1000),
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    candlestickSeries.setData(formatted);

    // Helper to align marker time to nearest candle time
    const getNearestCandleTime = (targetTimeMs, candles) => {
      const targetSec = Math.floor(targetTimeMs / 1000);
      const nearest = candles.reduce((prev, curr) => {
        const prevSec = Math.floor(prev.timestamp / 1000);
        const currSec = Math.floor(curr.timestamp / 1000);
        return Math.abs(currSec - targetSec) < Math.abs(prevSec - targetSec) ? curr : prev;
      }, candles[0]);
      return Math.floor(nearest.timestamp / 1000);
    };

    if (Array.isArray(dcaMarkers)) {
      // Normalize dcaMarkers time to UNIX seconds
      const normalizedMarkers = dcaMarkers.map((m) => ({
        ...m,
        time: Math.floor(m.time / 1000),
      }));
      formattedMarkersRef.current = normalizedMarkers
        .filter((m) => m.time)
        .map((m, i) => {
          const isFire = m.decision === "FIRE";
          const alignedTime = getNearestCandleTime(m.time * 1000, data); // convert back to ms
          return {
            time: alignedTime,
            position: isFire ? "aboveBar" : "belowBar",
            color: isFire ? "red" : "green",
            shape: isFire ? "arrowDown" : "circle",
            text: isFire ? "FIRE" : `DCA ${i + 1}`,
          };
        });
      candlestickSeries.setMarkers(formattedMarkersRef.current);
    }

    chartRef.current.subscribeClick((param) => {
      if (!param || !param.time || !data) return;

      const clickedTimestampSec = param.time;
      const index = data.findIndex(d => Math.floor(d.timestamp / 1000) === clickedTimestampSec);
      if (index !== -1) {
        setSelectedIndex(index);
        const clicked = data[index];
        onCandleClick?.(clicked.timestamp); // timestamp stays in ms
      }
    });

    return () => chartRef.current?.remove();
  }, [data, dimensions, onCandleClick, dcaMarkers]);

  useEffect(() => {
    if (selectedIndex !== null && data[selectedIndex] && seriesRef.current) {
      const point = data[selectedIndex];
      const time = Math.floor(point.timestamp / 1000);
      const baseMarkers = formattedMarkersRef.current || [];
      seriesRef.current.setMarkers([
        ...baseMarkers,
        {
          time,
          position: "aboveBar",
          color: "red",
          shape: "arrowDown",
          text: "Selected",
        },
      ]);

      onCandleClick?.(point.timestamp);
    }
  }, [selectedIndex, data, onCandleClick]);

  return (
    <div>
      <div ref={containerRef} style={{ width: "100%", height: "400px" }} />
    </div>
  );
};

export default CandleChart;
