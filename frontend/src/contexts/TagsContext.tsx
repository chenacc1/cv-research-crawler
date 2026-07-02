import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { TagDetail, CreateTagRequest, UpdateTagRequest } from '../types/tag';
import { listTags, createTag as apiCreateTag, updateTag as apiUpdateTag, deleteTag as apiDeleteTag } from '../api/tags';

interface TagsContextValue {
  tags: TagDetail[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
  createTag: (body: CreateTagRequest) => Promise<TagDetail>;
  updateTag: (id: string, body: UpdateTagRequest) => Promise<TagDetail>;
  deleteTag: (id: string) => Promise<void>;
}

const TagsContext = createContext<TagsContextValue | null>(null);

export function TagsProvider({ children }: { children: ReactNode }) {
  const [tags, setTags] = useState<TagDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trigger, setTrigger] = useState(0);

  const refetch = useCallback(() => setTrigger((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    listTags()
      .then((data) => {
        if (!cancelled) setTags(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message || 'Failed to load tags');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [trigger]);

  const createTag = useCallback(
    async (body: CreateTagRequest): Promise<TagDetail> => {
      const created = await apiCreateTag(body);
      refetch();
      return created;
    },
    [refetch],
  );

  const updateTag = useCallback(
    async (id: string, body: UpdateTagRequest): Promise<TagDetail> => {
      const updated = await apiUpdateTag(id, body);
      refetch();
      return updated;
    },
    [refetch],
  );

  const deleteTag = useCallback(
    async (id: string): Promise<void> => {
      await apiDeleteTag(id);
      refetch();
    },
    [refetch],
  );

  return (
    <TagsContext.Provider value={{ tags, loading, error, refetch, createTag, updateTag, deleteTag }}>
      {children}
    </TagsContext.Provider>
  );
}

export function useTagsContext(): TagsContextValue {
  const ctx = useContext(TagsContext);
  if (!ctx) {
    throw new Error('useTagsContext must be used within a TagsProvider');
  }
  return ctx;
}
