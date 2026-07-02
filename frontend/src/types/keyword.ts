export interface CrawlKeyword {
  id: string;
  keyword: string;
  enabled: boolean;
}

export interface KeywordListResponse {
  items: CrawlKeyword[];
}

export interface ExpandRequest {
  topic: string;
}

export interface ExpandResponse {
  keywords: string[];
}

export interface BatchAddRequest {
  keywords: string[];
}

export interface ToggleRequest {
  enabled: boolean;
}
