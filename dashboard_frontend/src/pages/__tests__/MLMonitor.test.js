import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import MLMonitor from '../MLMonitor';

// Mock fetch
global.fetch = jest.fn();

// Mock fetch
global.fetch = jest.fn();

describe('MLMonitor', () => {
  beforeEach(() => {
    fetch.mockClear();
    // Mock successful fetch response
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        models: [
          {
            name: 'safu_exit',
            type: 'binary_classification',
            accuracy: 0.85,
            status: 'active',
            last_trained: '2024-01-01T08:00:00Z'
          }
        ],
        predictions: [
          {
            id: 'pred_1',
            symbol: 'BTCUSDT',
            model_type: 'safu_exit',
            prediction: 0.85,
            confidence: 0.92,
            timestamp: '2024-01-01T10:00:00Z'
          }
        ],
        performance: {
          total_predictions: 1000,
          average_accuracy: 0.83,
          active_models: 3
        }
      })
    });
  });

  it('renders loading state initially', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<MLMonitor />);
    
    expect(screen.getByText('🤖 ML Monitor')).toBeInTheDocument();
    expect(screen.getByText('Loading ML status...')).toBeInTheDocument();
  });

  it('renders error state when fetch fails', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));
    
    render(<MLMonitor />);
    
    await waitFor(() => {
      expect(screen.getByText('Error: Network error')).toBeInTheDocument();
    });
  });

  it('renders ML data when fetch succeeds', async () => {
    const mockData = {
      models: [
        {
          name: 'Test Model',
          status: 'active',
          accuracy: 0.85,
          lastUpdated: '2024-01-01T00:00:00Z',
          version: '1.0.0'
        }
      ],
      predictions: [
        {
          symbol: 'BTCUSDT',
          timestamp: '2024-01-01T00:00:00Z',
          confidence: 0.75,
          recoveryOdds: 0.60,
          safuScore: 0.80,
          dcaSpend: 100.50
        }
      ],
      metrics: {
        totalPredictions: 100,
        averageAccuracy: 0.82,
        activeModels: 1
      }
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });
    
    render(<MLMonitor />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Model')).toBeInTheDocument();
      expect(screen.getByText('active')).toBeInTheDocument();
      expect(screen.getByText('85.0%')).toBeInTheDocument();
      expect(screen.getByText('BTCUSDT')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  it('renders empty state when no data available', async () => {
    const mockData = {
      models: [],
      predictions: [],
      metrics: {
        totalPredictions: 0,
        averageAccuracy: 0,
        activeModels: 0
      }
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });
    
    render(<MLMonitor />);
    
    await waitFor(() => {
      expect(screen.getByText('No recent predictions available')).toBeInTheDocument();
    });
  });

  it('auto-refreshes data every 30 seconds', async () => {
    jest.useFakeTimers();
    
    const mockData = {
      models: [],
      predictions: [],
      metrics: { totalPredictions: 0, averageAccuracy: 0, activeModels: 0 }
    };

    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    });
    
    render(<MLMonitor />);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    // Fast-forward 30 seconds
    jest.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    });

    jest.useRealTimers();
  });
});