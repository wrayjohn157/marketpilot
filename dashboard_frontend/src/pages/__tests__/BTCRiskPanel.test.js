import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import BTCRiskPanel from '../BTCRiskPanel';

// Mock fetch
global.fetch = jest.fn();

// Mock fetch
global.fetch = jest.fn();

describe('BTCRiskPanel', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders loading state initially', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<BTCRiskPanel />);
    
    expect(screen.getByText('⚠️ BTC Risk Panel')).toBeInTheDocument();
    expect(screen.getByText('Loading BTC data...')).toBeInTheDocument();
  });

  it('renders error state when fetch fails', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));
    
    await act(async () => {
      render(<BTCRiskPanel />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Error: Network error')).toBeInTheDocument();
    });
  });

  it('renders BTC data when fetch succeeds', async () => {
    const mockData = {
      risk_score: 0.6,
      price: 50000,
      price_change_24h: 2.5,
      rsi: 65,
      macd: 0.001,
      volume_24h: 1000000000,
      fear_greed_index: 45,
      market_cap: 1000000000000,
      recommendations: [
        {
          type: 'caution',
          title: 'High RSI',
          description: 'RSI is above 60, consider waiting for pullback'
        }
      ]
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });
    
    render(<BTCRiskPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Medium Risk')).toBeInTheDocument();
      expect(screen.getByText('60.0%')).toBeInTheDocument();
      expect(screen.getByText('$50,000.00')).toBeInTheDocument();
      expect(screen.getByText('+2.50% (24h)')).toBeInTheDocument();
      expect(screen.getByText('65.0')).toBeInTheDocument();
      expect(screen.getByText('High RSI')).toBeInTheDocument();
    });
  });

  it('displays correct risk level colors', async () => {
    const highRiskData = { risk_score: 0.8, price: 50000, price_change_24h: 0, rsi: 0, macd: 0, volume_24h: 0, fear_greed_index: 0, market_cap: 0, recommendations: [] };
    const lowRiskData = { risk_score: 0.2, price: 50000, price_change_24h: 0, rsi: 0, macd: 0, volume_24h: 0, fear_greed_index: 0, market_cap: 0, recommendations: [] };

    // Test high risk
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(highRiskData),
    });
    
    const { rerender } = render(<BTCRiskPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('High Risk')).toBeInTheDocument();
    });

    // Test low risk
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(lowRiskData),
    });
    
    rerender(<BTCRiskPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Low Risk')).toBeInTheDocument();
    });
  });

  it('renders empty recommendations when none available', async () => {
    const mockData = {
      risk_score: 0.5,
      price: 50000,
      price_change_24h: 0,
      rsi: 50,
      macd: 0,
      volume_24h: 0,
      fear_greed_index: 50,
      market_cap: 0,
      recommendations: []
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });
    
    render(<BTCRiskPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('No specific recommendations at this time')).toBeInTheDocument();
    });
  });

  it('auto-refreshes data every minute', async () => {
    jest.useFakeTimers();
    
    const mockData = {
      risk_score: 0.5,
      price: 50000,
      price_change_24h: 0,
      rsi: 50,
      macd: 0,
      volume_24h: 0,
      fear_greed_index: 50,
      market_cap: 0,
      recommendations: []
    };

    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    });
    
    render(<BTCRiskPanel />);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    // Fast-forward 60 seconds
    jest.advanceTimersByTime(60000);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    });

    jest.useRealTimers();
  });
});