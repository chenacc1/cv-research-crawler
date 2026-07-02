// ---- Pagination ----
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ---- API Error ----
export interface ApiErrorDetail {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

export interface NormalizedApiError extends Error {
  code: string;
  details: Record<string, unknown>;
  status: number;
}

// ---- Category ----
export interface CategoryRef {
  id: string;
  name: string;
  source: string;
}

export interface CategoryWithCount {
  id: string;
  name: string;
  source: string;
  paper_count: number;
}

// ---- Language count for stats ----
export interface LanguageCount {
  language: string;
  repo_count: number;
}

// ---- Category count for stats ----
export interface CategoryCount {
  name: string;
  paper_count: number;
}
