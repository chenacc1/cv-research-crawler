import apiClient from './client';
import type { PaginatedResponse } from '../types/common';
import type { CrawlLogEntry, CrawlStatusResponse, CrawlTriggerResponse, CrawlLogQueryParams } from '../types/crawl';

function buildLogParams(params: CrawlLogQueryParams): Record<string, string> {
  const p: Record<string, string> = {};
  if (params.page) p.page = String(params.page);
  if (params.page_size) p.page_size = String(params.page_size);
  if (params.source) p.source = params.source;
  if (params.status) p.status = params.status;
  if (params.sort) p.sort = params.sort;
  return p;
}

export async function listCrawlLogs(params: CrawlLogQueryParams = {}): Promise<PaginatedResponse<CrawlLogEntry>> {
  const { data } = await apiClient.get<PaginatedResponse<CrawlLogEntry>>('/crawls/logs', {
    params: buildLogParams(params),
  });
  return data;
}

export async function getCrawlStatus(): Promise<CrawlStatusResponse> {
  const { data } = await apiClient.get<CrawlStatusResponse>('/crawls/status');
  return data;
}

export async function triggerCrawl(source: string): Promise<CrawlTriggerResponse> {
  const { data } = await apiClient.post<CrawlTriggerResponse>(`/crawls/trigger/${source}`);
  return data;
}
