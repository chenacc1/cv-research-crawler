import { useState, useEffect, useCallback } from 'react';
import type { ReportSummary, ReportQueryParams } from '../types/report';
import type { PaginatedResponse } from '../types/common';
import { listReports } from '../api/reports';

interface UseReportsResult {
  reports: ReportSummary[];
  total: number;
  pages: number;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useReports(params: ReportQueryParams): UseReportsResult {
  const [data, setData] = useState<Pick<UseReportsResult, 'reports' | 'total' | 'pages'>>({
    reports: [],
    total: 0,
    pages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trigger, setTrigger] = useState(0);

  const refetch = useCallback(() => setTrigger((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    listReports(params)
      .then((res: PaginatedResponse<ReportSummary>) => {
        if (!cancelled) {
          setData({ reports: res.items, total: res.total, pages: res.pages });
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message || 'Failed to load reports');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(params), trigger]);

  return { ...data, loading, error, refetch };
}
