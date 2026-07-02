// ---- Tag Ref (minimal reference) ----
export interface TagRef {
  id: string;
  name: string;
  color: string;
}

// ---- Tag Detail (full with counts) ----
export interface TagDetail {
  id: string;
  name: string;
  color: string;
  paper_count: number;
  repo_count: number;
  created_at: string;
}

// ---- Create Tag Request ----
export interface CreateTagRequest {
  name: string;
  color: string;
}

// ---- Update Tag Request ----
export interface UpdateTagRequest {
  name?: string;
  color?: string;
}

// ---- Set Tags Request (for paper/repo tag update) ----
export interface SetTagsRequest {
  tag_ids: string[];
}

// ---- Set Tags Response ----
export interface SetTagsResponse {
  paper_id?: string;
  repo_id?: string;
  tags: TagRef[];
}
