import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import './tailwind.css'; // ✅ Make sure this is correct

// Pages
import TradeDashboard from "./pages/TradeDashboard.jsx"
import ActiveTrades from "./pages/ActiveTrades";
import ScanReview from "./pages/ScanReview";
import DCATracker from "./pages/DcaTracker";
import BacktestSummary from "./pages/BacktestSummary";
import MLMonitor from "./pages/MLMonitor";
import BTCRiskPanel from "./pages/BTCRiskPanel";
import ForkScore from "./pages/ForkScore";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-950 text-white">
        <div className="md:flex">
          <Sidebar />
          <main className="flex-1 p-6 overflow-y-auto">
            <Routes>
              <Route path="/trade-dashboard" element={<TradeDashboard />} />
              <Route path="/active-trades" element={<ActiveTrades />} />
              <Route path="/scan-review" element={<ScanReview />} />
              <Route path="/dca-tracker" element={<DCATracker />} />
              <Route path="/backtest-summary" element={<BacktestSummary />} />
              <Route path="/ml-monitor" element={<MLMonitor />} />
              <Route path="/btc-panel" element={<BTCRiskPanel />} />
              <Route path="/fork-score" element={<ForkScore />} />
              <Route path="*" element={<Navigate to="/trade-dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
