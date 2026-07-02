import apiClient from './client';
import type { PaginatedResponse } from '../types/common';
import type { AuthorSummary, AuthorWithPapers } from '../types/paper';

export async function listAuthors(params: { page?: number; page_size?: number; q?: string } = {}): Promise<PaginatedResponse<AuthorSummary>> {
  const p: Record<string, string> = {};
  if (params.page) p.page = String(params.page);
  if (params.page_size) p.page_size = String(params.page_size);
  if (params.q) p.q = params.q;
  const { data } = await apiClient.get<PaginatedResponse<AuthorSummary>>('/authors', { params: p });
  return data;
}

export async function getAuthor(id: string): Promise<AuthorWithPapers> {
  const { data } = await apiClient.get<AuthorWithPapers>(`/authors/${id}`);
  return data;
}
