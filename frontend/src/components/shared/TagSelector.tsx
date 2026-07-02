import { useState, useRef, useEffect } from 'react';
import type { TagRef } from '../../types/tag';
import { tagBadgeStyle } from './TagBadge';

interface TagSelectorProps {
  availableTags: TagRef[];
  selectedTagIds: string[];
  onChange: (tagIds: string[]) => void;
  placeholder?: string;
}

export default function TagSelector({ availableTags, selectedTagIds, onChange, placeholder = 'Select tags...' }: TagSelectorProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedTags = availableTags.filter((t) => selectedTagIds.includes(t.id));
  const filtered = availableTags.filter(
    (t) => !selectedTagIds.includes(t.id) && t.name.toLowerCase().includes(search.toLowerCase()),
  );

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  function toggleTag(tag: TagRef) {
    if (selectedTagIds.includes(tag.id)) onChange(selectedTagIds.filter((id) => id !== tag.id));
    else onChange([...selectedTagIds, tag.id]);
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="glass-input flex min-h-[38px] flex-wrap items-center gap-1 cursor-pointer h-auto py-1 px-2"
        onClick={() => setOpen(!open)}>
        {selectedTags.map((tag) => (
          <span key={tag.id} className="inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-xs font-medium"
            style={tagBadgeStyle(tag.color)}>
            {tag.name}
            <button type="button" onClick={(e) => { e.stopPropagation(); toggleTag(tag); }}
              className="ml-0.5 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full hover:bg-black/10">&times;</button>
          </span>
        ))}
        <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>{selectedTags.length === 0 ? placeholder : ''}</span>
      </div>
      {open && (
        <div className="absolute z-20 mt-1 w-full glass-panel bg-white/80" style={{ padding: 4 }}>
          <input type="text" className="w-full px-3 py-2 text-sm outline-none bg-transparent"
            style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}
            placeholder="Search tags..." value={search}
            onChange={(e) => setSearch(e.target.value)} onClick={(e) => e.stopPropagation()} />
          <div className="max-h-48 overflow-y-auto p-1">
            {filtered.length === 0 ? (
              <p className="px-2 py-2 text-sm" style={{ color: 'var(--text-tertiary)' }}>No tags found</p>
            ) : (
              filtered.map((tag) => (
                <button key={tag.id} type="button"
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm hover:bg-white/15"
                  onClick={(e) => { e.stopPropagation(); toggleTag(tag); }}>
                  <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: tag.color }} />
                  {tag.name}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
