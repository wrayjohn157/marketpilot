import React from 'react';
import { render, screen } from '@testing-library/react';
import BTCRiskPanel from '../BTCRiskPanel';

// Mock fetch
global.fetch = jest.fn();

describe('BTCRiskPanel', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders BTC Risk Panel title', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<BTCRiskPanel />);

    expect(screen.getByText('⚠️ BTC Risk Panel')).toBeInTheDocument();
  });

  it('renders loading state initially', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<BTCRiskPanel />);

    expect(screen.getByText('Loading BTC data...')).toBeInTheDocument();
  });
});
