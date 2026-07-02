import { useState, useEffect, useCallback } from 'react';
import type { PaperSummary, PaperQueryParams } from '../types/paper';
import type { PaginatedResponse } from '../types/common';
import { listPapers } from '../api/papers';

interface UsePapersResult {
  papers: PaperSummary[];
  total: number;
  pages: number;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function usePapers(params: PaperQueryParams): UsePapersResult {
  const [data, setData] = useState<Pick<UsePapersResult, 'papers' | 'total' | 'pages'>>({
    papers: [],
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

    listPapers(params)
      .then((res: PaginatedResponse<PaperSummary>) => {
        if (!cancelled) {
          setData({ papers: res.items, total: res.total, pages: res.pages });
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message || 'Failed to load papers');
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
