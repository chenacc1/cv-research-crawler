type StatusVariant = 'success' | 'delivered' | 'partial' | 'running' | 'pending' | 'failed' | string;

function getBadgeClass(status: StatusVariant): string {
  switch (status) {
    case 'success': case 'delivered': case 'ok': return 'glass-badge glass-badge-success';
    case 'partial': case 'running': case 'pending': return 'glass-badge glass-badge-warning';
    case 'failed': return 'glass-badge glass-badge-error';
    default: return 'glass-badge glass-badge-default';
  }
}

interface StatusBadgeProps { status: StatusVariant; label?: string; }

export default function StatusBadge({ status, label }: StatusBadgeProps) {
  return (
    <span className={getBadgeClass(status)}>
      <span className={`h-1.5 w-1.5 rounded-full ${
        status === 'success' || status === 'delivered' ? 'bg-green-500' :
        status === 'failed' ? 'bg-red-500' :
        status === 'partial' || status === 'running' || status === 'pending' ? 'bg-yellow-500' : 'bg-gray-400'
      }`} />
      {label || status}
    </span>
  );
}
