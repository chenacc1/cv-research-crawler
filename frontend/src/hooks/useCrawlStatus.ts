import { useState, useEffect, useCallback } from 'react';
import type { CrawlLogEntry, CrawlJobStatus, CrawlLogQueryParams } from '../types/crawl';
import type { PaginatedResponse } from '../types/common';
import { listCrawlLogs, getCrawlStatus as apiGetStatus, triggerCrawl as apiTrigger } from '../api/crawls';

interface UseCrawlStatusResult {
  logs: CrawlLogEntry[];
  jobs: CrawlJobStatus[];
  totalLogs: number;
  loading: boolean;
  error: string | null;
  triggerCrawl: (source: string) => Promise<string>;
}

export function useCrawlStatus(
  logParams: CrawlLogQueryParams = { page: 1, page_size: 20 },
): UseCrawlStatusResult {
  const [logs, setLogs] = useState<CrawlLogEntry[]>([]);
  const [jobs, setJobs] = useState<CrawlJobStatus[]>([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trigger, setTrigger] = useState(0);

  const refetch = useCallback(() => setTrigger((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([listCrawlLogs(logParams), apiGetStatus()])
      .then(([logRes, statusRes]: [PaginatedResponse<CrawlLogEntry>, { jobs: CrawlJobStatus[] }]) => {
        if (!cancelled) {
          setLogs(logRes.items);
          setTotalLogs(logRes.total);
          setJobs(statusRes.jobs);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message || 'Failed to load crawl status');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(logParams), trigger]);

  const triggerCrawl = useCallback(
    async (source: string): Promise<string> => {
      const res = await apiTrigger(source);
      refetch();
      return res.message;
    },
    [refetch],
  );

  return { logs, jobs, totalLogs, loading, error, triggerCrawl };
}
