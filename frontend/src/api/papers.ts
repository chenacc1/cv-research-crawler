import apiClient from './client';
import type { PaginatedResponse } from '../types/common';
import type { PaperSummary, PaperDetail, PaperQueryParams } from '../types/paper';
import type { SetTagsRequest, SetTagsResponse } from '../types/tag';

function buildParams(params: PaperQueryParams): Record<string, string | string[]> {
  const p: Record<string, string | string[]> = {};
  if (params.page) p.page = String(params.page);
  if (params.page_size) p.page_size = String(params.page_size);
  if (params.source?.length) p.source = params.source;
  if (params.category?.length) p.category = params.category;
  if (params.date_from) p.date_from = params.date_from;
  if (params.date_to) p.date_to = params.date_to;
  if (params.q) p.q = params.q;
  if (params.tag_id?.length) p.tag_id = params.tag_id;
  if (params.sort) p.sort = params.sort;
  if (params.venue) p.venue = params.venue;
  return p;
}

export async function listPapers(params: PaperQueryParams = {}): Promise<PaginatedResponse<PaperSummary>> {
  const { data } = await apiClient.get<PaginatedResponse<PaperSummary>>('/papers', {
    params: buildParams(params),
    paramsSerializer: { indexes: null },
  });
  return data;
}

export async function getPaper(id: string): Promise<PaperDetail> {
  const { data } = await apiClient.get<PaperDetail>(`/papers/${id}`);
  return data;
}

export async function setPaperTags(id: string, tagIds: string[]): Promise<SetTagsResponse> {
  const body: SetTagsRequest = { tag_ids: tagIds };
  const { data } = await apiClient.put<SetTagsResponse>(`/papers/${id}/tags`, body);
  return data;
}
