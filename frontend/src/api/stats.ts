import apiClient from './client';
import type { StatsResponse, HealthResponse } from '../types/stats';

export async function getStats(): Promise<StatsResponse> {
  const { data } = await apiClient.get<StatsResponse>('/stats');
  return data;
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health');
  return data;
}
