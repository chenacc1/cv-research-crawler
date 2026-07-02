interface LoadingSkeletonProps {
  rows?: number;
  variant?: 'card' | 'table-row' | 'detail' | 'text';
}

export default function LoadingSkeleton({ rows = 5, variant = 'table-row' }: LoadingSkeletonProps) {
  if (variant === 'card') {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="glass-card p-4">
            <div className="glass-skeleton mb-3 h-5 w-3/4" />
            <div className="glass-skeleton mb-2 h-4 w-1/2" />
            <div className="glass-skeleton mb-3 h-4 w-full" />
            <div className="flex gap-2">
              <div className="glass-skeleton h-6 w-16 rounded-full" />
              <div className="glass-skeleton h-6 w-12 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'detail') {
    return (
      <div className="space-y-4">
        <div className="glass-skeleton h-8 w-2/3" />
        <div className="glass-skeleton h-4 w-1/3" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="glass-skeleton h-4" style={{ width: `${95 - i * 15}%` }} />
        ))}
      </div>
    );
  }

  if (variant === 'text') {
    return (
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="glass-skeleton h-4" style={{ width: `${80 - i * 10}%` }} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="glass-panel flex items-center gap-4 p-3">
          <div className="glass-skeleton h-4 flex-1" />
          <div className="glass-skeleton h-4 w-20" />
          <div className="glass-skeleton h-4 w-16" />
          <div className="glass-skeleton h-6 w-16 rounded-full" />
        </div>
      ))}
    </div>
  );
}
