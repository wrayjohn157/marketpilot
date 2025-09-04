import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, X, Check } from 'lucide-react';

const OnboardingTour = ({ isOpen, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const tourSteps = [
    {
      title: 'Welcome to Market7!',
      content: 'This tour will help you get familiar with the Market7 trading dashboard. You can skip this tour anytime or restart it from the help menu.',
      target: null,
      position: 'center'
    },
    {
      title: 'Account Summary',
      content: 'Here you can see your current balance, today\'s P&L, active trades count, and total trading volume. This gives you a quick overview of your trading performance.',
      target: '.account-summary',
      position: 'bottom'
    },
    {
      title: 'Active Trades Panel',
      content: 'Monitor all your open positions here. You can see real-time P&L, DCA status, and risk levels for each trade. Click on any trade to see detailed information.',
      target: '.active-trades',
      position: 'left'
    },
    {
      title: 'Performance Metrics',
      content: 'Track your trading performance with key metrics like success rate, Sharpe ratio, and maximum drawdown. These help you evaluate your trading strategy.',
      target: '.performance-metrics',
      position: 'top'
    },
    {
      title: 'Navigation Menu',
      content: 'Use this menu to access different features: Trading for trade management, ML Monitor for AI insights, BTC Risk Panel for market analysis, and more.',
      target: '.navigation-menu',
      position: 'right'
    },
    {
      title: 'Settings & Configuration',
      content: 'Configure your trading parameters, API keys, and preferences in the Settings section. This is where you\'ll set up your trading strategy.',
      target: '.settings-button',
      position: 'bottom'
    },
    {
      title: 'Help & Support',
      content: 'Access help documentation, tutorials, and contact support. The help system includes searchable guides and troubleshooting tips.',
      target: '.help-button',
      position: 'bottom'
    },
    {
      title: 'Tour Complete!',
      content: 'You\'re all set! Start by configuring your API keys in Settings, then explore the different features. Remember, you can always access help from the help menu.',
      target: null,
      position: 'center'
    }
  ];

  const nextStep = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const skipTour = () => {
    onComplete();
  };

  const currentStepData = tourSteps[currentStep];

  useEffect(() => {
    if (isOpen && currentStepData.target) {
      const element = document.querySelector(currentStepData.target);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [isOpen, currentStep, currentStepData.target]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black bg-opacity-50" />

      {/* Highlight */}
      {currentStepData.target && (
        <div className="absolute inset-0 pointer-events-none">
          <div
            className="absolute bg-white bg-opacity-20 rounded-lg border-2 border-blue-500 shadow-lg"
            style={{
              top: currentStepData.target ? '50%' : '50%',
              left: currentStepData.target ? '50%' : '50%',
              transform: 'translate(-50%, -50%)',
              width: currentStepData.target ? '300px' : '400px',
              height: currentStepData.target ? '200px' : '300px'
            }}
          />
        </div>
      )}

      {/* Tooltip */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div
          className={`bg-white rounded-lg shadow-xl p-6 max-w-md mx-4 pointer-events-auto ${
            currentStepData.position === 'center' ? 'text-center' : ''
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {currentStepData.title}
            </h3>
            <button
              onClick={skipTour}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Content */}
          <p className="text-gray-600 mb-6 whitespace-pre-line">
            {currentStepData.content}
          </p>

          {/* Progress */}
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-500 mb-2">
              <span>Step {currentStep + 1} of {tourSteps.length}</span>
              <span>{Math.round(((currentStep + 1) / tourSteps.length) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentStep + 1) / tourSteps.length) * 100}%` }}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <button
              onClick={prevStep}
              disabled={currentStep === 0}
              className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                currentStep === 0
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <ChevronLeft size={16} className="mr-1" />
              Previous
            </button>

            <div className="flex space-x-2">
              {currentStep < tourSteps.length - 1 ? (
                <button
                  onClick={nextStep}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Next
                  <ChevronRight size={16} className="ml-1" />
                </button>
              ) : (
                <button
                  onClick={onComplete}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Check size={16} className="mr-1" />
                  Get Started
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingTour;
