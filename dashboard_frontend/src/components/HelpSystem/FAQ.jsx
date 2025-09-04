import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Search } from 'lucide-react';

const FAQ = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [openItems, setOpenItems] = useState(new Set());

  const faqData = [
    {
      category: 'Getting Started',
      questions: [
        {
          question: 'What is Market7?',
          answer: 'Market7 is an AI-powered cryptocurrency trading system that combines machine learning, smart DCA (Dollar-Cost Averaging) strategies, and advanced risk management for automated trading.'
        },
        {
          question: 'How do I get started?',
          answer: '1. Configure your API keys in Settings\n2. Set up your trading parameters\n3. Enable the DCA system\n4. Start monitoring your trades\n5. Use the help system for detailed guidance'
        },
        {
          question: 'Is Market7 free to use?',
          answer: 'Yes, Market7 is open-source software. You can use it for free, but you\'ll need API keys for exchanges (3Commas, Binance) to trade with real money.'
        },
        {
          question: 'What exchanges does Market7 support?',
          answer: 'Market7 currently supports 3Commas and Binance exchanges through their APIs. More exchanges may be added in future updates.'
        }
      ]
    },
    {
      category: 'Trading Features',
      questions: [
        {
          question: 'How does the DCA system work?',
          answer: 'The DCA (Dollar-Cost Averaging) system analyzes losing trades and makes intelligent decisions about when to add to positions to improve your average entry price. It uses ML models to determine optimal timing and volume.'
        },
        {
          question: 'What is the SAFU system?',
          answer: 'SAFU (Safe Exit) is a risk management system that automatically exits trades when certain risk conditions are met. It helps protect your capital by implementing stop-loss orders and other safety measures.'
        },
        {
          question: 'How accurate are the ML predictions?',
          answer: 'ML model accuracy varies by market conditions, but typically ranges from 60-80% for binary classifications. The system continuously learns and improves from new data.'
        },
        {
          question: 'Can I customize the trading strategies?',
          answer: 'Yes, Market7 is highly customizable. You can modify existing strategies, create your own, and adjust parameters to match your trading style and risk tolerance.'
        }
      ]
    },
    {
      category: 'Technical Issues',
      questions: [
        {
          question: 'The dashboard is not loading. What should I do?',
          answer: '1. Check if the backend is running\n2. Clear your browser cache\n3. Check browser console for errors\n4. Try refreshing the page\n5. Restart the services if needed'
        },
        {
          question: 'My trades are not executing. Why?',
          answer: '1. Verify your API keys are valid and have trading permissions\n2. Check your account has sufficient balance\n3. Ensure trading is enabled in settings\n4. Check for error messages in the logs\n5. Verify your exchange account is active'
        },
        {
          question: 'The DCA system is not working. What\'s wrong?',
          answer: '1. Check if DCA is enabled in settings\n2. Verify DCA parameters are configured correctly\n3. Check if risk thresholds are met\n4. Ensure ML confidence levels are sufficient\n5. Check if there are any error messages'
        },
        {
          question: 'I\'m getting API errors. What should I do?',
          answer: '1. Verify your API keys are correct and not expired\n2. Check your internet connection\n3. Ensure you haven\'t exceeded API rate limits\n4. Verify your exchange account is in good standing\n5. Check the API status page for your exchange'
        }
      ]
    },
    {
      category: 'Configuration',
      questions: [
        {
          question: 'How do I configure my API keys?',
          answer: '1. Go to Settings > API Configuration\n2. Enter your 3Commas API key and secret\n3. Enter your Binance API key and secret\n4. Test the connections\n5. Save your configuration'
        },
        {
          question: 'What trading parameters should I set?',
          answer: 'Start with conservative settings:\n- Max position size: 1-5% of your account\n- Daily loss limit: 2-5% of your account\n- DCA max attempts: 3-5\n- Risk threshold: 0.7-0.8\n- Adjust based on your risk tolerance'
        },
        {
          question: 'How do I set up notifications?',
          answer: '1. Go to Settings > Notifications\n2. Configure email settings\n3. Set up Slack webhook (optional)\n4. Choose which alerts to receive\n5. Test your notification settings'
        },
        {
          question: 'Can I paper trade first?',
          answer: 'Yes, Market7 supports paper trading for testing strategies without real money. Enable paper trading mode in settings to test your configuration safely.'
        }
      ]
    },
    {
      category: 'Performance & Monitoring',
      questions: [
        {
          question: 'How do I monitor my trading performance?',
          answer: 'Use the Performance Metrics section to track:\n- Success rate and win/loss ratio\n- Sharpe ratio and risk-adjusted returns\n- Maximum drawdown\n- Total return and P&L\n- Use the ML Monitor for AI insights'
        },
        {
          question: 'What should I do if performance is poor?',
          answer: '1. Review your trading parameters\n2. Check if market conditions have changed\n3. Analyze your trade history for patterns\n4. Consider adjusting your strategy\n5. Use the backtesting feature to test changes'
        },
        {
          question: 'How often should I check the system?',
          answer: 'For automated trading, check daily for:\n- System health and alerts\n- Performance metrics\n- Any error messages\n- Market conditions\n- Adjust parameters as needed based on performance'
        },
        {
          question: 'Can I export my trading data?',
          answer: 'Yes, you can export:\n- Trade history as CSV/Excel\n- Performance reports\n- Configuration settings\n- Log files for analysis\n- Use the Export Data feature in the dashboard'
        }
      ]
    },
    {
      category: 'Security & Safety',
      questions: [
        {
          question: 'Is Market7 safe to use?',
          answer: 'Market7 includes comprehensive risk management features, but trading cryptocurrencies always involves risk. Use appropriate position sizing, never risk more than you can afford to lose, and always test with small amounts first.'
        },
        {
          question: 'How do I secure my API keys?',
          answer: '1. Use environment variables for API keys\n2. Never share your API keys\n3. Use read-only keys when possible\n4. Regularly rotate your keys\n5. Monitor API key usage'
        },
        {
          question: 'What if I lose access to my account?',
          answer: '1. Keep backups of your configuration\n2. Document your API key recovery process\n3. Use strong passwords and 2FA\n4. Keep your exchange account recovery information safe\n5. Contact support if needed'
        },
        {
          question: 'Can I run Market7 on a VPS?',
          answer: 'Yes, Market7 is designed to run on VPS providers like DigitalOcean, AWS, or Google Cloud. Follow the installation guide for VPS deployment.'
        }
      ]
    }
  ];

  const filteredData = faqData.map(category => ({
    ...category,
    questions: category.questions.filter(q =>
      q.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.answer.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.questions.length > 0);

  const toggleItem = (categoryIndex, questionIndex) => {
    const key = `${categoryIndex}-${questionIndex}`;
    const newOpenItems = new Set(openItems);
    if (newOpenItems.has(key)) {
      newOpenItems.delete(key);
    } else {
      newOpenItems.add(key);
    }
    setOpenItems(newOpenItems);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Frequently Asked Questions</h2>
        <p className="text-gray-600 mb-6">
          Find answers to common questions about Market7. Can't find what you're looking for? 
          <a href="mailto:support@market7.local" className="text-blue-600 hover:text-blue-800 ml-1">
            Contact our support team
          </a>.
        </p>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search FAQ..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      <div className="space-y-8">
        {filteredData.map((category, categoryIndex) => (
          <div key={categoryIndex} className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900">{category.category}</h3>
            </div>
            
            <div className="divide-y divide-gray-200">
              {category.questions.map((item, questionIndex) => {
                const key = `${categoryIndex}-${questionIndex}`;
                const isOpen = openItems.has(key);
                
                return (
                  <div key={questionIndex} className="p-6">
                    <button
                      onClick={() => toggleItem(categoryIndex, questionIndex)}
                      className="w-full text-left flex items-center justify-between focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 rounded-lg p-2 -m-2"
                    >
                      <h4 className="text-lg font-medium text-gray-900 pr-4">
                        {item.question}
                      </h4>
                      {isOpen ? (
                        <ChevronUp className="text-gray-500 flex-shrink-0" size={20} />
                      ) : (
                        <ChevronDown className="text-gray-500 flex-shrink-0" size={20} />
                      )}
                    </button>
                    
                    {isOpen && (
                      <div className="mt-4 pl-2">
                        <p className="text-gray-600 whitespace-pre-line leading-relaxed">
                          {item.answer}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {filteredData.length === 0 && searchQuery && (
        <div className="text-center py-12">
          <Search className="mx-auto text-gray-400 mb-4" size={48} />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-600">
            Try searching with different keywords or browse the categories above.
          </p>
        </div>
      )}

      <div className="mt-12 bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Still need help?</h3>
        <p className="text-blue-800 mb-4">
          Can't find the answer you're looking for? Our support team is here to help.
        </p>
        <div className="flex flex-wrap gap-4">
          <a
            href="mailto:support@market7.local"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Email Support
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
          >
            API Documentation
          </a>
          <a
            href="https://github.com/your-username/market7"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
          >
            GitHub Issues
          </a>
        </div>
      </div>
    </div>
  );
};

export default FAQ;