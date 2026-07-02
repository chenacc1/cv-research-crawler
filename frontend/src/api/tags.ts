import apiClient from './client';
import type { TagDetail, CreateTagRequest, UpdateTagRequest } from '../types/tag';

export async function listTags(): Promise<TagDetail[]> {
  const { data } = await apiClient.get<{ items: TagDetail[] }>('/tags');
  return data.items;
}

export async function createTag(body: CreateTagRequest): Promise<TagDetail> {
  const { data } = await apiClient.post<TagDetail>('/tags', body);
  return data;
}

export async function updateTag(id: string, body: UpdateTagRequest): Promise<TagDetail> {
  const { data } = await apiClient.put<TagDetail>(`/tags/${id}`, body);
  return data;
}

export async function deleteTag(id: string): Promise<void> {
  await apiClient.delete(`/tags/${id}`);
}
