import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getReport, retryReport } from '../api/reports';
import type { ReportDetail } from '../types/report';
import StatusBadge from '../components/shared/StatusBadge';
import MarkdownViewer from '../components/shared/MarkdownViewer';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import { useI18n } from '../i18n/I18nProvider';

export default function ReportViewPage() {
  const { t } = useI18n();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [regenerateMsg, setRegenerateMsg] = useState('');

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    getReport(id)
      .then((data) => { if (!cancelled) setReport(data); })
      .catch((err: Error) => { if (!cancelled) setError(err.message || 'Failed to load report'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  async function handleRetry() {
    if (!id) return;
    setRegenerating(true);
    setRegenerateMsg('');
    try {
      const data = await retryReport(id);
      setReport(data);
      setRegenerateMsg('Report regenerated successfully.');
    } catch (err) {
      setRegenerateMsg((err as Error).message || 'Failed to regenerate');
    } finally {
      setRegenerating(false);
    }
  }

  if (loading) return <LoadingSkeleton variant="detail" />;

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <p className="mb-2 text-red-700">{error}</p>
        <button type="button" onClick={() => navigate(-1)} className="text-sm text-blue-600 hover:underline">
          Go back
        </button>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="space-y-6">
      <button
        type="button"
        onClick={() => navigate('/reports')}
        className="text-sm text-blue-600 hover:underline"
      >
        &larr; {t('reports.backToList')}
      </button>

      {/* Report metadata header */}
      <div className="glass-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              {report.type === 'daily' ? t('reports.daily') : t('reports.weekly')} Report
            </h1>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">
              {report.date_range_start} -- {report.date_range_end}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={report.delivery_status} />
            <button
              type="button"
              onClick={handleRetry}
              disabled={regenerating}
              className="glass-btn glass-btn-primary glass-btn-sm"
            >
              {regenerating ? t('reports.regenerating') : t('reports.regenerate')}
            </button>
          </div>
        </div>

        <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="text-xs text-[var(--text-secondary)]">{t('reports.papers')}</p>
            <p className="font-medium text-[var(--text-primary)]">{report.paper_count}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-secondary)]">{t('reports.repos')}</p>
            <p className="font-medium text-[var(--text-primary)]">{report.repo_count}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-secondary)]">{t('reports.generated')}</p>
            <p className="font-medium text-[var(--text-primary)]">{new Date(report.generated_at).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-secondary)]">{t('reports.file')}</p>
            <p className="font-medium text-[var(--text-primary)] truncate">{report.file_path}</p>
          </div>
        </div>

        {regenerateMsg && (
          <p className={`mt-2 text-sm ${regenerateMsg.includes('success') ? 'text-green-600' : 'text-red-600'}`}>
            {regenerateMsg}
          </p>
        )}
      </div>

      {/* Markdown content */}
      <div className="glass-panel p-6">
        <MarkdownViewer content={report.content} />
      </div>
    </div>
  );
}
