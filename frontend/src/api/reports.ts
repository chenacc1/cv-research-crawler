import apiClient from './client';
import type { PaginatedResponse } from '../types/common';
import type { ReportSummary, ReportDetail, ReportQueryParams } from '../types/report';

function buildParams(params: ReportQueryParams): Record<string, string> {
  const p: Record<string, string> = {};
  if (params.page) p.page = String(params.page);
  if (params.page_size) p.page_size = String(params.page_size);
  if (params.type) p.type = params.type;
  if (params.sort) p.sort = params.sort;
  return p;
}

export async function listReports(params: ReportQueryParams = {}): Promise<PaginatedResponse<ReportSummary>> {
  const { data } = await apiClient.get<PaginatedResponse<ReportSummary>>('/reports', {
    params: buildParams(params),
  });
  return data;
}

export async function getReport(id: string): Promise<ReportDetail> {
  const { data } = await apiClient.get<ReportDetail>(`/reports/${id}`);
  return data;
}

export async function retryReport(id: string): Promise<ReportDetail> {
  const { data } = await apiClient.post<ReportDetail>(`/reports/${id}/retry`);
  return data;
}
