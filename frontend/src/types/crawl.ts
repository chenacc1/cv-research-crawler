// ---- Crawl Log Entry ----
export interface CrawlLogEntry {
  id: string;
  source: string;
  started_at: string;
  finished_at: string | null;
  items_found: number;
  items_new: number;
  items_updated: number;
  status: 'running' | 'success' | 'partial' | 'failed';
  error_message: string | null;
}

// ---- Crawl Job Status ----
export interface CrawlJobStatus {
  source: string;
  enabled: boolean;
  interval_minutes: number | null;
  cron: string | null;
  last_run: string | null;
  next_run: string | null;
  last_status: string | null;
}

// ---- Crawl Status Response ----
export interface CrawlStatusResponse {
  jobs: CrawlJobStatus[];
}

// ---- Crawl Trigger Response ----
export interface CrawlTriggerResponse {
  source: string;
  message: string;
  triggered_at: string;
}

// ---- Crawl Log Query Params ----
export interface CrawlLogQueryParams {
  page?: number;
  page_size?: number;
  source?: string;
  status?: string;
  sort?: string;
}
