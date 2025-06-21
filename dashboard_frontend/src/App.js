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
import DcaConfig from "./pages/DcaConfig";
import TvScreenerConfig from "./pages/TvScreenerConfig";
import SafuConfig from "./pages/SafuConfig";
import AskGpt from "./pages/AskGpt";
import CodeEditor from "./pages/GptCodeEditor";

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
              <Route path="/ask-gpt" element={<AskGpt />} />
              <Route path="/code-editor" element={<CodeEditor />} />
              <Route path="/ml-monitor" element={<MLMonitor />} />
              <Route path="/btc-panel" element={<BTCRiskPanel />} />
              <Route path="/fork-score" element={<ForkScore />} />
              <Route path="/dca-config" element={<DcaConfig />} />
              <Route path="/tv-config" element={<TvScreenerConfig />} />
              <Route path="/safu-config" element={<SafuConfig />} />
              <Route path="*" element={<Navigate to="/trade-dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
