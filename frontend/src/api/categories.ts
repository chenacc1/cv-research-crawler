import apiClient from './client';
import type { CategoryWithCount } from '../types/common';

export async function listCategories(source?: string): Promise<CategoryWithCount[]> {
  const params: Record<string, string> = {};
  if (source) params.source = source;
  const { data } = await apiClient.get<{ items: CategoryWithCount[] }>('/categories', { params });
  return data.items;
}
