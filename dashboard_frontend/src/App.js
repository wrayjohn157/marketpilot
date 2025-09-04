import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import './tailwind.css'; // ✅ Make sure this is correct

// Pages
import ActiveTrades from "./pages/ActiveTrades";
import AskGpt from "./pages/AskGpt";
import BacktestSummary from "./pages/BacktestSummary";
import BTCRiskPanel from "./pages/BTCRiskPanel";
import DcaConfig from "./pages/DcaConfig";
import DCATracker from "./pages/DcaTracker";
import ForkScore from "./pages/ForkScore";
import CodeEditor from "./pages/GptCodeEditor";
import MLMonitor from "./pages/MLMonitor";
import SafuConfig from "./pages/SafuConfig";
import ScanReview from "./pages/ScanReview";
import TradeDashboard from "./pages/TradeDashboard.jsx";
import TvScreenerConfig from "./pages/TvScreenerConfig";
import DcaStrategyBuilder from "./pages/DcaStrategyBuilder";
import SimulationPage from "./pages/SimulationPage";

// Help System
import HelpModal from "./components/HelpSystem/HelpModal";
import OnboardingTour from "./components/HelpSystem/OnboardingTour";
import FAQ from "./components/HelpSystem/FAQ";
import { useState, useEffect } from "react";

function App() {
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [showOnboardingTour, setShowOnboardingTour] = useState(false);
  const [hasCompletedTour, setHasCompletedTour] = useState(false);

  // Check if user has completed onboarding tour
  useEffect(() => {
    const tourCompleted = localStorage.getItem('market7-tour-completed');
    if (!tourCompleted) {
      setShowOnboardingTour(true);
    }
  }, []);

  const handleTourComplete = () => {
    setShowOnboardingTour(false);
    setHasCompletedTour(true);
    localStorage.setItem('market7-tour-completed', 'true');
  };

  return (
    <Router>
      <div className="min-h-screen bg-gray-950 text-white">
        <div className="md:flex">
          <Sidebar
            onHelpClick={() => setShowHelpModal(true)}
            onTourClick={() => setShowOnboardingTour(true)}
          />
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
              <Route path="/dca-tuner" element={<DcaStrategyBuilder />} />
              <Route path="/simulation" element={<SimulationPage />} />
              <Route path="/faq" element={<FAQ />} />
              <Route path="*" element={<Navigate to="/trade-dashboard" replace />} />
            </Routes>
          </main>
        </div>

        {/* Help System */}
        <HelpModal
          isOpen={showHelpModal}
          onClose={() => setShowHelpModal(false)}
        />

        <OnboardingTour
          isOpen={showOnboardingTour}
          onClose={() => setShowOnboardingTour(false)}
          onComplete={handleTourComplete}
        />
      </div>
    </Router>
  );
}

export default App;
