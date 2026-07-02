import React from 'react';
import type { TagRef } from '../../types/tag';

export function tagBadgeStyle(color: string): React.CSSProperties {
  return { backgroundColor: `${color}2A`, color, borderColor: `${color}55` };
}

interface TagBadgeProps {
  tag: TagRef;
  onRemove?: () => void;
  size?: 'sm' | 'md';
  onClick?: () => void;
}

export default function TagBadge({ tag, onRemove, size = 'md', onClick }: TagBadgeProps) {
  const sizeClass = size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-sm px-2 py-0.5';

  return (
    <span
      className={`glass-tag ${onClick ? 'cursor-pointer hover:opacity-80' : ''} ${onRemove ? 'pr-1' : ''} ${sizeClass}`}
      style={{
        backgroundColor: `${tag.color}2A`,
        color: tag.color,
        borderColor: `${tag.color}55`,
      }}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter') onClick(); } : undefined}
    >
      <span
        className={`inline-block rounded-full ${size === 'sm' ? 'h-1.5 w-1.5' : 'h-2 w-2'}`}
        style={{ backgroundColor: tag.color }}
      />
      {tag.name}
      {onRemove && (
        <button type="button" onClick={(e) => { e.stopPropagation(); onRemove(); }}
          className="ml-0.5 inline-flex h-4 w-4 items-center justify-center rounded-full hover:bg-black/10"
          aria-label={`Remove tag ${tag.name}`}
        >&times;</button>
      )}
    </span>
  );
}
