import React, { useState } from 'react';
import { X, Search, BookOpen, Video, MessageCircle, ExternalLink } from 'lucide-react';

const HelpModal = ({ isOpen, onClose }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSection, setActiveSection] = useState('overview');

  const helpSections = {
    overview: {
      title: 'Getting Started',
      content: [
        {
          title: 'Welcome to Market7',
          description: 'Market7 is an AI-powered cryptocurrency trading system that combines machine learning, smart DCA strategies, and advanced risk management.',
          icon: '🚀'
        },
        {
          title: 'Dashboard Overview',
          description: 'The main dashboard shows your account summary, active trades, and performance metrics. Use the navigation menu to access different features.',
          icon: '📊'
        },
        {
          title: 'Quick Start',
          description: '1. Configure your API keys in Settings\n2. Set up your trading parameters\n3. Enable the DCA system\n4. Start monitoring your trades',
          icon: '⚡'
        }
      ]
    },
    trading: {
      title: 'Trading Features',
      content: [
        {
          title: 'Smart DCA System',
          description: 'The DCA (Dollar-Cost Averaging) system automatically rescues losing trades by buying more at lower prices to improve your average entry price.',
          icon: '💰'
        },
        {
          title: 'Risk Management',
          description: 'The SAFU system provides automated risk management with stop-loss orders, take-profit targets, and position sizing controls.',
          icon: '🛡️'
        },
        {
          title: 'ML Predictions',
          description: 'Machine learning models analyze market conditions and provide confidence scores for trading decisions.',
          icon: '🤖'
        }
      ]
    },
    dashboard: {
      title: 'Dashboard Guide',
      content: [
        {
          title: 'Account Summary',
          description: 'View your current balance, today\'s P&L, active trades count, and total trading volume.',
          icon: '💳'
        },
        {
          title: 'Active Trades',
          description: 'Monitor your open positions with real-time P&L, DCA status, and risk levels.',
          icon: '📈'
        },
        {
          title: 'Performance Metrics',
          description: 'Track your trading performance with success rates, Sharpe ratio, and drawdown metrics.',
          icon: '📊'
        }
      ]
    },
    settings: {
      title: 'Configuration',
      content: [
        {
          title: 'API Keys',
          description: 'Configure your 3Commas and Binance API keys to enable trading functionality.',
          icon: '🔑'
        },
        {
          title: 'Trading Parameters',
          description: 'Set position sizes, risk limits, and trading hours to match your strategy.',
          icon: '⚙️'
        },
        {
          title: 'DCA Settings',
          description: 'Configure DCA attempts, volume scaling, and risk thresholds.',
          icon: '🔄'
        }
      ]
    },
    troubleshooting: {
      title: 'Troubleshooting',
      content: [
        {
          title: 'Dashboard Not Loading',
          description: 'Check if the backend is running, clear your browser cache, and try refreshing the page.',
          icon: '🔧'
        },
        {
          title: 'Trades Not Executing',
          description: 'Verify your API keys are valid, check account balance, and ensure trading is enabled.',
          icon: '⚠️'
        },
        {
          title: 'DCA Not Working',
          description: 'Check if DCA is enabled, verify settings, and ensure risk thresholds are met.',
          icon: '❌'
        }
      ]
    }
  };

  const filteredContent = helpSections[activeSection]?.content.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.description.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Help & Documentation</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <div className="flex h-[600px]">
          {/* Sidebar */}
          <div className="w-64 bg-gray-50 border-r p-4">
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                <input
                  type="text"
                  placeholder="Search help..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <nav className="space-y-2">
              {Object.entries(helpSections).map(([key, section]) => (
                <button
                  key={key}
                  onClick={() => setActiveSection(key)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    activeSection === key
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {section.title}
                </button>
              ))}
            </nav>

            <div className="mt-8 pt-4 border-t">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Quick Links</h3>
              <div className="space-y-2">
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-sm text-blue-600 hover:text-blue-800"
                >
                  <ExternalLink size={14} className="mr-2" />
                  API Documentation
                </a>
                <a
                  href="https://github.com/your-username/market7"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-sm text-blue-600 hover:text-blue-800"
                >
                  <ExternalLink size={14} className="mr-2" />
                  GitHub Repository
                </a>
                <a
                  href="mailto:support@market7.local"
                  className="flex items-center text-sm text-blue-600 hover:text-blue-800"
                >
                  <MessageCircle size={14} className="mr-2" />
                  Contact Support
                </a>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="mb-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {helpSections[activeSection]?.title}
              </h3>
              <p className="text-gray-600">
                {activeSection === 'overview' && 'Get started with Market7 trading system'}
                {activeSection === 'trading' && 'Learn about trading features and strategies'}
                {activeSection === 'dashboard' && 'Navigate and use the dashboard effectively'}
                {activeSection === 'settings' && 'Configure your trading parameters and preferences'}
                {activeSection === 'troubleshooting' && 'Solve common issues and problems'}
              </p>
            </div>

            <div className="space-y-6">
              {filteredContent.map((item, index) => (
                <div key={index} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-start">
                    <span className="text-2xl mr-3">{item.icon}</span>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900 mb-2">{item.title}</h4>
                      <p className="text-gray-600 whitespace-pre-line">{item.description}</p>
                    </div>
                  </div>
                </div>
              ))}

              {filteredContent.length === 0 && searchQuery && (
                <div className="text-center py-8">
                  <Search className="mx-auto text-gray-400 mb-4" size={48} />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
                  <p className="text-gray-600">
                    Try searching with different keywords or browse the sections above.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpModal;
