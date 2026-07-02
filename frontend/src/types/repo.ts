import type { TagRef } from './tag';

// ---- Repo Summary (list item) ----
export interface RepoSummary {
  id: string;
  full_name: string;
  description: string | null;
  url: string;
  stars: number;
  forks: number;
  language: string | null;
  topics: string[];
  pushed_at: string | null;
  crawled_at: string;
  last_crawled_at: string;
  tags: TagRef[];
  summary_cn: string | null;
  summary_en: string | null;
}

// ---- Repo Detail (same as summary in V1) ----
export type RepoDetail = RepoSummary;

// ---- Repo Query Params ----
export interface RepoQueryParams {
  page?: number;
  page_size?: number;
  language?: string[];
  topic?: string[];
  stars_min?: number;
  stars_max?: number;
  pushed_after?: string;
  pushed_before?: string;
  tag_id?: string[];
  q?: string;
  sort?: string;
}
