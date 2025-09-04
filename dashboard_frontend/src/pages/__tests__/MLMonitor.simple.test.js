import React from 'react';
import { render, screen } from '@testing-library/react';
import MLMonitor from '../MLMonitor';

// Mock fetch
global.fetch = jest.fn();

describe('MLMonitor', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders ML Monitor title', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<MLMonitor />);
    
    expect(screen.getByText('🤖 ML Monitor')).toBeInTheDocument();
  });

  it('renders loading state initially', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<MLMonitor />);
    
    expect(screen.getByText('Loading ML status...')).toBeInTheDocument();
  });
});