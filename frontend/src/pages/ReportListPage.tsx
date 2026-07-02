import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useReports } from '../hooks/useReports';
import type { ReportQueryParams } from '../types/report';
import Pagination from '../components/shared/Pagination';
import GlassDropdown from '../components/shared/GlassDropdown';
import StatusBadge from '../components/shared/StatusBadge';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import { useI18n } from '../i18n/I18nProvider';

export default function ReportListPage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [type, setType] = useState<'daily' | 'weekly' | ''>('');
  const [sort, setSort] = useState('-generated_at');

  const params: ReportQueryParams = useMemo(
    () => ({
      page,
      page_size: 20,
      type: (type as ReportQueryParams['type']) || undefined,
      sort,
    }),
    [page, type, sort],
  );

  const { reports, total, pages, loading, error } = useReports(params);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t('reports.title')}</h1>

      {/* Simple filters */}
      <div className="flex flex-wrap items-center gap-3">
        <GlassDropdown
          value={type}
          options={[{ value: '', label: t('reports.allTypes') }, { value: 'daily', label: t('reports.daily') }, { value: 'weekly', label: t('reports.weekly') }]}
          onChange={(v) => { setType(v as 'daily' | 'weekly' | ''); setPage(1); }}
          className="min-w-[140px]"
        />
        <GlassDropdown
          value={sort}
          options={[{ value: '-generated_at', label: t('reports.newest') }, { value: 'generated_at', label: t('reports.oldest') }]}
          onChange={(v) => setSort(v)}
          className="min-w-[160px]"
        />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      {loading && <LoadingSkeleton variant="table-row" rows={8} />}

      {!loading && !error && reports.length === 0 && (
        <div className="glass-panel p-12 text-center">
          <p className="text-[var(--text-secondary)]">{t('reports.noReports')}</p>
        </div>
      )}

      {!loading && reports.length > 0 && (
        <>
          <div className="glass-panel overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-[rgba(0,0,0,0.06)] bg-white/20">
                <tr>
                  <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('reports.type')}</th>
                  <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('reports.dateRange')}</th>
                  <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('reports.papers')}</th>
                  <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('reports.repos')}</th>
                  <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('reports.status')}</th>
                  <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('reports.generated')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[rgba(0,0,0,0.06)]">
                {reports.map((report) => (
                  <tr key={report.id} className="hover:bg-white/20">
                    <td className="px-4 py-3">
                      <Link to={`/reports/${report.id}`} className="text-blue-600 hover:underline">
                        <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${
                          report.type === 'daily' ? 'bg-blue-50 text-blue-700' : 'bg-purple-50 text-purple-700'
                        }`}>
                          {report.type}
                        </span>
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-[var(--text-primary)]">
                      <Link to={`/reports/${report.id}`} className="hover:underline">
                        {report.date_range_start} to {report.date_range_end}
                      </Link>
                    </td>
                    <td className="px-4 py-3 font-medium text-[var(--text-primary)]">{report.paper_count}</td>
                    <td className="px-4 py-3 font-medium text-[var(--text-primary)]">{report.repo_count}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={report.delivery_status} />
                    </td>
                    <td className="px-4 py-3 text-[var(--text-secondary)]">
                      {new Date(report.generated_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
