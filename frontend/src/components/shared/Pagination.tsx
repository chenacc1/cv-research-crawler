interface PaginationProps {
  page: number;
  pages: number;
  total: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, pages, total, onPageChange }: PaginationProps) {
  if (pages <= 1) return null;

  const maxVisible = 5;
  let start = Math.max(1, page - Math.floor(maxVisible / 2));
  const end = Math.min(pages, start + maxVisible - 1);
  if (end - start + 1 < maxVisible) start = Math.max(1, end - maxVisible + 1);
  const pageNumbers = Array.from({ length: end - start + 1 }, (_, i) => start + i);

  return (
    <div className="flex items-center justify-between pt-4" style={{ borderTop: '1px solid rgba(0,0,0,0.06)' }}>
      <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
        {total} items
      </span>
      <div className="flex items-center gap-1.5">
        <button type="button" disabled={page <= 1} onClick={() => onPageChange(page - 1)} className="glass-page">‹</button>
        {start > 1 && (
          <>
            <button type="button" onClick={() => onPageChange(1)} className="glass-page">1</button>
            {start > 2 && <span className="px-1 text-sm" style={{ color: 'var(--text-tertiary)' }}>…</span>}
          </>
        )}
        {pageNumbers.map((n) => (
          <button key={n} type="button" onClick={() => onPageChange(n)} className={n === page ? 'glass-page glass-page-active' : 'glass-page'}>{n}</button>
        ))}
        {end < pages && (
          <>
            {end < pages - 1 && <span className="px-1 text-sm" style={{ color: 'var(--text-tertiary)' }}>…</span>}
            <button type="button" onClick={() => onPageChange(pages)} className="glass-page">{pages}</button>
          </>
        )}
        <button type="button" disabled={page >= pages} onClick={() => onPageChange(page + 1)} className="glass-page">›</button>
      </div>
    </div>
  );
}
