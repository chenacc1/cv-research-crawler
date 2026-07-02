import type { ReactNode } from 'react';
import FilterChip from './FilterChip';

export interface ActiveFilter {
  label: string;
  value: string;
  onRemove: () => void;
}

interface FilterBarProps {
  filters: ActiveFilter[];
  children: ReactNode;
}

export default function FilterBar({ filters, children }: FilterBarProps) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-end gap-3">{children}</div>
      {filters.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Active filters:</span>
          {filters.map((f, i) => (
            <FilterChip key={`${f.label}-${f.value}-${i}`} label={f.label} value={f.value} onRemove={f.onRemove} />
          ))}
        </div>
      ) : (
        <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>No active filters</p>
      )}
    </div>
  );
}
