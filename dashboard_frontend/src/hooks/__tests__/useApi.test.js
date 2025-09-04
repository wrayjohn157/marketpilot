import { renderHook, waitFor } from '@testing-library/react';
import { useApi, useRealtimeData, usePaginatedData } from '../useApi';

// Mock fetch
global.fetch = jest.fn();

describe('useApi', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('should fetch data successfully', async () => {
    const mockData = { id: 1, name: 'Test' };
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve(mockData),
    });

    const apiCall = () => fetch('/api/test').then(res => res.json());
    const { result } = renderHook(() => useApi(apiCall));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBe(null);
    expect(result.current.error).toBe(null);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBe(null);
  });

  it('should handle fetch errors', async () => {
    const mockError = new Error('Fetch failed');
    fetch.mockRejectedValueOnce(mockError);

    const apiCall = () => fetch('/api/test').then(res => res.json());
    const { result } = renderHook(() => useApi(apiCall));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBe(null);
    expect(result.current.error).toBe('Fetch failed');
  });

  it('should refetch data when refetch is called', async () => {
    const mockData = { id: 1, name: 'Test' };
    fetch.mockResolvedValue({
      json: () => Promise.resolve(mockData),
    });

    const apiCall = () => fetch('/api/test').then(res => res.json());
    const { result } = renderHook(() => useApi(apiCall));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(fetch).toHaveBeenCalledTimes(1);

    result.current.refetch();

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });
});

describe('useRealtimeData', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    fetch.mockClear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should auto-refresh data at specified interval', async () => {
    const mockData = { id: 1, name: 'Test' };
    fetch.mockResolvedValue({
      json: () => Promise.resolve(mockData),
    });

    const apiCall = () => fetch('/api/test').then(res => res.json());
    const { result } = renderHook(() => useRealtimeData(apiCall, 1000));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(fetch).toHaveBeenCalledTimes(1);

    // Fast-forward time
    jest.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });
});

describe('usePaginatedData', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('should load initial page', async () => {
    const mockData = {
      data: [{ id: 1 }, { id: 2 }],
      hasMore: true,
    };
    fetch.mockResolvedValue({
      json: () => Promise.resolve(mockData),
    });

    const apiCall = (page, pageSize) =>
      fetch(`/api/test?page=${page}&size=${pageSize}`).then(res => res.json());

    const { result } = renderHook(() => usePaginatedData(apiCall, 1, 10));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual([{ id: 1 }, { id: 2 }]);
    expect(result.current.hasMore).toBe(true);
  });

  it('should load more data when loadMore is called', async () => {
    const mockData1 = {
      data: [{ id: 1 }, { id: 2 }],
      hasMore: true,
    };
    const mockData2 = {
      data: [{ id: 3 }, { id: 4 }],
      hasMore: false,
    };

    fetch
      .mockResolvedValueOnce({
        json: () => Promise.resolve(mockData1),
      })
      .mockResolvedValueOnce({
        json: () => Promise.resolve(mockData2),
      });

    const apiCall = (page, pageSize) =>
      fetch(`/api/test?page=${page}&size=${pageSize}`).then(res => res.json());

    const { result } = renderHook(() => usePaginatedData(apiCall, 1, 10));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual([{ id: 1 }, { id: 2 }]);
    expect(result.current.hasMore).toBe(true);

    result.current.loadMore();

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual([{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }]);
    expect(result.current.hasMore).toBe(false);
  });
});
