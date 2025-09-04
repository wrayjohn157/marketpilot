import React from 'react';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../layout/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    render(<LoadingSpinner />);

    expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument();
  });

  it('renders with custom text', () => {
    render(<LoadingSpinner text="Loading data..." />);

    expect(screen.getByText('Loading data...')).toBeInTheDocument();
  });

  it('renders with different sizes', () => {
    const { rerender } = render(<LoadingSpinner size="sm" />);
    expect(screen.getByRole('status', { hidden: true })).toHaveClass('w-4', 'h-4');

    rerender(<LoadingSpinner size="lg" />);
    expect(screen.getByRole('status', { hidden: true })).toHaveClass('w-12', 'h-12');
  });

  it('renders without text when text is empty', () => {
    render(<LoadingSpinner text="" />);

    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<LoadingSpinner className="custom-class" />);

    expect(screen.getByRole('status', { hidden: true })).toHaveClass('custom-class');
  });
});
