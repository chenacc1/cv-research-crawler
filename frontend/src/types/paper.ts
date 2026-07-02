import type { CategoryRef } from './common';
import type { TagRef } from './tag';

// ---- Author Ref ----
export interface AuthorRef {
  id: string;
  name: string;
  affiliation: string | null;
  author_order: number;
}

// ---- Paper Summary (list item) ----
export interface PaperSummary {
  id: string;
  title: string;
  source: string;
  source_id: string;
  venue: string | null;
  published_date: string | null;
  url: string;
  pdf_url: string | null;
  code_url: string | null;
  crawled_at: string;
  updated_at: string;
  categories: CategoryRef[];
  tags: TagRef[];
  author_names: string[];
  summary_cn: string | null;
  summary_en: string | null;
}

// ---- Paper Detail (full detail) ----
export interface PaperDetail extends PaperSummary {
  abstract: string | null;
  authors: AuthorRef[];
  merged_into_id: string | null;
  versions: PaperVersionRef[];
}

// ---- Paper Version Ref ----
export interface PaperVersionRef {
  id: string;
  title: string;
  source: string;
  url: string;
}

// ---- Author Paper Ref ----
export interface AuthorPaperRef {
  id: string;
  title: string;
  published_date: string | null;
  source: string;
  author_order: number;
}

// ---- Author With Papers ----
export interface AuthorWithPapers {
  id: string;
  name: string;
  affiliation: string | null;
  papers: AuthorPaperRef[];
}

// ---- Author Summary (list item) ----
export interface AuthorSummary {
  id: string;
  name: string;
  affiliation: string | null;
  paper_count: number;
}

// ---- Paper Query Params ----
export interface PaperQueryParams {
  page?: number;
  page_size?: number;
  source?: string[];
  category?: string[];
  date_from?: string;
  date_to?: string;
  q?: string;
  tag_id?: string[];
  sort?: string;
  venue?: string;
}
