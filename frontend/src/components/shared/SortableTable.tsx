import type { ReactNode } from 'react';

export interface SortableColumn { key: string; label: string; sortable?: boolean; }

interface SortableTableProps {
  columns: SortableColumn[]; sortKey: string; sortDir: 'asc' | 'desc';
  onSort: (key: string) => void; children: ReactNode;
}

export default function SortableTable({ columns, sortKey, sortDir, onSort, children }: SortableTableProps) {
  return (
    <div className="glass-panel overflow-x-auto">
      <table className="glass-table w-full text-left text-sm">
        <thead>
          <tr>
            {columns.map((col) => {
              const isActive = col.sortable !== false && sortKey === col.key;
              return (
                <th key={col.key}
                  className={`px-4 py-3 ${col.sortable !== false ? 'cursor-pointer select-none hover:bg-white/20' : ''}`}
                  onClick={() => { if (col.sortable !== false) onSort(col.key); }}
                  aria-sort={isActive ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined}>
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {col.sortable !== false && (
                      <span className="inline-flex flex-col leading-none" style={{ color: 'var(--text-tertiary)' }}>
                        <span className={isActive && sortDir === 'asc' ? 'text-blue-600' : ''} style={{ fontSize: '0.6em', lineHeight: 1 }}>&#9650;</span>
                        <span className={isActive && sortDir === 'desc' ? 'text-blue-600' : ''} style={{ fontSize: '0.6em', lineHeight: 1, marginTop: '-2px' }}>&#9660;</span>
                      </span>
                    )}
                  </span>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
