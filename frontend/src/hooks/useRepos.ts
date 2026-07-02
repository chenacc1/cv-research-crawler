import { useState, useEffect, useCallback } from 'react';
import type { RepoSummary, RepoQueryParams } from '../types/repo';
import type { PaginatedResponse } from '../types/common';
import { listRepos } from '../api/repos';

interface UseReposResult {
  repos: RepoSummary[];
  total: number;
  pages: number;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useRepos(params: RepoQueryParams): UseReposResult {
  const [data, setData] = useState<Pick<UseReposResult, 'repos' | 'total' | 'pages'>>({
    repos: [],
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

    listRepos(params)
      .then((res: PaginatedResponse<RepoSummary>) => {
        if (!cancelled) {
          setData({ repos: res.items, total: res.total, pages: res.pages });
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message || 'Failed to load repos');
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
