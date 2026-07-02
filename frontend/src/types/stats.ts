import type { CategoryCount, LanguageCount } from './common';

// ---- Dashboard Stats ----
export interface PaperStats {
  total: number;
  by_source: Record<string, number>;
  new_today: number;
  new_this_week: number;
}

export interface RepoStats {
  total: number;
  new_today: number;
  new_this_week: number;
}

export interface TagStats {
  total: number;
}

export interface CrawlStats {
  last_arxiv: string | null;
  last_github: string | null;
  total_runs: number;
  success_rate: number;
}

export interface ReportStats {
  daily_count: number;
  weekly_count: number;
}

export interface StatsResponse {
  papers: PaperStats;
  repos: RepoStats;
  tags: TagStats;
  crawls: CrawlStats;
  reports: ReportStats;
  top_categories: CategoryCount[];
  top_languages: LanguageCount[];
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  database: string;
  scheduler: string;
  version: string;
}
