// ---- Report Summary (list item) ----
export interface ReportSummary {
  id: string;
  type: 'daily' | 'weekly';
  date_range_start: string;
  date_range_end: string;
  file_path: string;
  paper_count: number;
  repo_count: number;
  delivery_status: 'pending' | 'delivered' | 'failed';
  generated_at: string;
}

// ---- Report Detail (with content) ----
export interface ReportDetail extends ReportSummary {
  content: string;
}

// ---- Report Query Params ----
export interface ReportQueryParams {
  page?: number;
  page_size?: number;
  type?: 'daily' | 'weekly';
  sort?: string;
}
