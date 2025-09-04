import { useState, useEffect, useCallback } from 'react';
import apiClient from '../lib/api';

/**
 * Custom hook for API calls with loading states and error handling
 */
export const useApi = (apiCall, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err.message);
      console.error('API call failed:', err);
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
};

/**
 * Hook for real-time data with auto-refresh
 */
export const useRealtimeData = (apiCall, interval = 30000) => {
  const { data, loading, error, refetch } = useApi(apiCall);

  useEffect(() => {
    if (interval > 0) {
      const timer = setInterval(refetch, interval);
      return () => clearInterval(timer);
    }
  }, [refetch, interval]);

  return { data, loading, error, refetch };
};

/**
 * Hook for paginated data
 */
export const usePaginatedData = (apiCall, initialPage = 1, pageSize = 10) => {
  const [page, setPage] = useState(initialPage);
  const [allData, setAllData] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPage = useCallback(async (pageNum) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall(pageNum, pageSize);

      if (pageNum === 1) {
        setAllData(result.data || []);
      } else {
        setAllData(prev => [...prev, ...(result.data || [])]);
      }

      setHasMore(result.hasMore || false);
    } catch (err) {
      setError(err.message);
      console.error('Paginated API call failed:', err);
    } finally {
      setLoading(false);
    }
  }, [apiCall, pageSize]);

  useEffect(() => {
    fetchPage(page);
  }, [fetchPage, page]);

  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1);
    }
  }, [loading, hasMore]);

  const reset = useCallback(() => {
    setPage(1);
    setAllData([]);
    setHasMore(true);
  }, []);

  return {
    data: allData,
    loading,
    error,
    hasMore,
    loadMore,
    reset,
    refetch: () => fetchPage(page)
  };
};
