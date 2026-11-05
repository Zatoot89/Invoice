import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import toast from 'react-hot-toast';

interface AnalyticsOptions {
  dateRange?: number;
  period?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface AnalyticsData {
  dashboardData: any;
  revenueData: any;
  customerData: any;
  performanceData: any;
  loading: boolean;
  error: string | null;
}

export function useAnalytics(options: AnalyticsOptions = {}) {
  const {
    dateRange = 30,
    period = 'monthly',
    autoRefresh = false,
    refreshInterval = 300000 // 5 minutes
  } = options;

  const { user, token } = useAuth();
  const [data, setData] = useState<AnalyticsData>({
    dashboardData: null,
    revenueData: null,
    customerData: null,
    performanceData: null,
    loading: true,
    error: null,
  });

  const fetchAnalyticsData = useCallback(async (customOptions?: Partial<AnalyticsOptions>) => {
    if (!token) {
      setData(prev => ({ ...prev, loading: false, error: 'No authentication token' }));
      return;
    }

    const currentDateRange = customOptions?.dateRange ?? dateRange;
    const currentPeriod = customOptions?.period ?? period;

    setData(prev => ({ ...prev, loading: true, error: null }));

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      // Fetch dashboard data
      const dashboardResponse = await fetch(
        `${baseUrl}/api/v1/analytics/dashboard?date_range=${currentDateRange}`,
        { headers }
      );

      if (!dashboardResponse.ok) {
        throw new Error('Failed to fetch dashboard analytics');
      }

      const dashboardResult = await dashboardResponse.json();

      // Fetch revenue data
      const revenueResponse = await fetch(
        `${baseUrl}/api/v1/analytics/revenue?period=${currentPeriod}&months=12`,
        { headers }
      );

      if (!revenueResponse.ok) {
        throw new Error('Failed to fetch revenue analytics');
      }

      const revenueResult = await revenueResponse.json();

      // Fetch customer data
      const customerResponse = await fetch(
        `${baseUrl}/api/v1/analytics/customers?date_range=${currentDateRange * 6}`, // 6x for customer analytics
        { headers }
      );

      if (!customerResponse.ok) {
        throw new Error('Failed to fetch customer analytics');
      }

      const customerResult = await customerResponse.json();

      // Fetch performance data
      const performanceResponse = await fetch(
        `${baseUrl}/api/v1/analytics/performance?date_range=${currentDateRange * 3}`, // 3x for performance
        { headers }
      );

      if (!performanceResponse.ok) {
        throw new Error('Failed to fetch performance analytics');
      }

      const performanceResult = await performanceResponse.json();

      setData({
        dashboardData: dashboardResult.data,
        revenueData: revenueResult.data,
        customerData: customerResult.data,
        performanceData: performanceResult.data,
        loading: false,
        error: null,
      });

    } catch (error) {
      console.error('Analytics data fetch error:', error);
      setData(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch analytics data'
      }));
      toast.error('Failed to load analytics data');
    }
  }, [token, dateRange, period]);

  // Initial data fetch
  useEffect(() => {
    fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchAnalyticsData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchAnalyticsData]);

  const refreshData = useCallback((customOptions?: Partial<AnalyticsOptions>) => {
    fetchAnalyticsData(customOptions);
  }, [fetchAnalyticsData]);

  // Export analytics data
  const exportData = useCallback(async (
    reportType: 'dashboard' | 'revenue' | 'customers' | 'performance',
    formatType: 'json' | 'csv' | 'pdf' = 'json'
  ) => {
    if (!token) {
      toast.error('No authentication token');
      return null;
    }

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${baseUrl}/api/v1/analytics/export?report_type=${reportType}&format_type=${formatType}&date_range=${dateRange}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to export analytics data');
      }

      const result = await response.json();
      
      if (formatType === 'json') {
        // For JSON, return the data directly
        return result.data;
      } else {
        // For CSV/PDF, this would typically trigger a download
        toast.success('Export initiated');
        return result;
      }

    } catch (error) {
      console.error('Analytics export error:', error);
      toast.error('Failed to export analytics data');
      return null;
    }
  }, [token, dateRange]);

  // Get real-time metrics
  const getRealTimeMetrics = useCallback(async () => {
    if (!token) return null;

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${baseUrl}/api/v1/analytics/real-time`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch real-time metrics');
      }

      const result = await response.json();
      return result.data;

    } catch (error) {
      console.error('Real-time metrics error:', error);
      return null;
    }
  }, [token]);

  // Create analytics alert
  const createAlert = useCallback(async (
    metric: string,
    condition: string,
    threshold: number,
    notificationMethod: string = 'email'
  ) => {
    if (!token) {
      toast.error('No authentication token');
      return false;
    }

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${baseUrl}/api/v1/analytics/alerts`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            metric,
            condition,
            threshold,
            notification_method: notificationMethod
          })
        }
      );

      if (!response.ok) {
        throw new Error('Failed to create analytics alert');
      }

      const result = await response.json();
      toast.success('Analytics alert created successfully');
      return result.data;

    } catch (error) {
      console.error('Create alert error:', error);
      toast.error('Failed to create analytics alert');
      return false;
    }
  }, [token]);

  return {
    ...data,
    refreshData,
    exportData,
    getRealTimeMetrics,
    createAlert,
  };
}

// Specialized hooks for specific analytics data
export function useDashboardAnalytics(dateRange: number = 30) {
  const { dashboardData, loading, error, refreshData } = useAnalytics({ dateRange });
  
  return {
    data: dashboardData,
    loading,
    error,
    refresh: () => refreshData({ dateRange })
  };
}

export function useRevenueAnalytics(period: string = 'monthly', months: number = 12) {
  const { revenueData, loading, error, refreshData } = useAnalytics({ period });
  
  return {
    data: revenueData,
    loading,
    error,
    refresh: () => refreshData({ period })
  };
}

export function useCustomerAnalytics(dateRange: number = 180) {
  const { customerData, loading, error, refreshData } = useAnalytics({ dateRange });
  
  return {
    data: customerData,
    loading,
    error,
    refresh: () => refreshData({ dateRange })
  };
}

export function usePerformanceAnalytics(dateRange: number = 90) {
  const { performanceData, loading, error, refreshData } = useAnalytics({ dateRange });
  
  return {
    data: performanceData,
    loading,
    error,
    refresh: () => refreshData({ dateRange })
  };
}

// Real-time analytics hook
export function useRealTimeAnalytics(refreshInterval: number = 30000) {
  const [realTimeData, setRealTimeData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { getRealTimeMetrics } = useAnalytics();

  const fetchRealTimeData = useCallback(async () => {
    setLoading(true);
    const data = await getRealTimeMetrics();
    setRealTimeData(data);
    setLoading(false);
  }, [getRealTimeMetrics]);

  useEffect(() => {
    fetchRealTimeData();

    const interval = setInterval(fetchRealTimeData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchRealTimeData, refreshInterval]);

  return {
    data: realTimeData,
    loading,
    refresh: fetchRealTimeData
  };
}