import apiClient from './client';
import type { PaginatedResponse } from '../types/common';
import type { RepoSummary, RepoDetail, RepoQueryParams } from '../types/repo';
import type { SetTagsRequest, SetTagsResponse } from '../types/tag';

function buildParams(params: RepoQueryParams): Record<string, string | string[]> {
  const p: Record<string, string | string[]> = {};
  if (params.page) p.page = String(params.page);
  if (params.page_size) p.page_size = String(params.page_size);
  if (params.language?.length) p.language = params.language;
  if (params.topic?.length) p.topic = params.topic;
  if (params.stars_min !== undefined) p.stars_min = String(params.stars_min);
  if (params.stars_max !== undefined) p.stars_max = String(params.stars_max);
  if (params.pushed_after) p.pushed_after = params.pushed_after;
  if (params.pushed_before) p.pushed_before = params.pushed_before;
  if (params.tag_id?.length) p.tag_id = params.tag_id;
  if (params.q) p.q = params.q;
  if (params.sort) p.sort = params.sort;
  return p;
}

export async function listRepos(params: RepoQueryParams = {}): Promise<PaginatedResponse<RepoSummary>> {
  const { data } = await apiClient.get<PaginatedResponse<RepoSummary>>('/repos', {
    params: buildParams(params),
    paramsSerializer: { indexes: null },
  });
  return data;
}

export async function getRepo(id: string): Promise<RepoDetail> {
  const { data } = await apiClient.get<RepoDetail>(`/repos/${id}`);
  return data;
}

export async function setRepoTags(id: string, tagIds: string[]): Promise<SetTagsResponse> {
  const body: SetTagsRequest = { tag_ids: tagIds };
  const { data } = await apiClient.put<SetTagsResponse>(`/repos/${id}/tags`, body);
  return data;
}
