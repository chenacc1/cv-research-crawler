import apiClient from './client';
import type { CrawlKeyword, KeywordListResponse, ExpandRequest, ExpandResponse, BatchAddRequest, ToggleRequest } from '../types/keyword';

export async function listKeywords(): Promise<CrawlKeyword[]> {
  const { data } = await apiClient.get<KeywordListResponse>('/crawl-keywords');
  return data.items;
}

export async function expandKeywords(topic: string): Promise<string[]> {
  const { data } = await apiClient.post<ExpandResponse>('/crawl-keywords/expand', { topic } as ExpandRequest, {
    timeout: 120000, // LLM expansion can take a while
  });
  return data.keywords;
}

export async function batchAddKeywords(keywords: string[]): Promise<CrawlKeyword[]> {
  const { data } = await apiClient.post<KeywordListResponse>('/crawl-keywords/batch', { keywords } as BatchAddRequest);
  return data.items;
}

export async function toggleKeyword(id: string, enabled: boolean): Promise<CrawlKeyword> {
  const { data } = await apiClient.put<CrawlKeyword>(`/crawl-keywords/${id}`, { enabled } as ToggleRequest);
  return data;
}

export async function deleteKeyword(id: string): Promise<void> {
  await apiClient.delete(`/crawl-keywords/${id}`);
}
