import { useState, useMemo } from 'react';
import { useCrawlStatus } from '../hooks/useCrawlStatus';
import Pagination from '../components/shared/Pagination';
import StatusBadge from '../components/shared/StatusBadge';
import SortableTable, { type SortableColumn } from '../components/shared/SortableTable';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import GlassDropdown from '../components/shared/GlassDropdown';
import { useI18n } from '../i18n/I18nProvider';

const LOG_COLUMNS_ZH: SortableColumn[] = [
  { key: 'source', label: '来源', sortable: true },
  { key: 'started_at', label: '开始时间', sortable: true },
  { key: 'finished_at', label: '结束时间', sortable: true },
  { key: 'items_found', label: '找到', sortable: true },
  { key: 'items_new', label: '新增', sortable: true },
  { key: 'items_updated', label: '更新', sortable: true },
  { key: 'status', label: '状态', sortable: true },
  { key: 'error_message', label: '错误', sortable: false },
];
const LOG_COLUMNS_EN: SortableColumn[] = [
  { key: 'source', label: 'Source', sortable: true },
  { key: 'started_at', label: 'Started', sortable: true },
  { key: 'finished_at', label: 'Finished', sortable: true },
  { key: 'items_found', label: 'Found', sortable: true },
  { key: 'items_new', label: 'New', sortable: true },
  { key: 'items_updated', label: 'Updated', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'error_message', label: 'Error', sortable: false },
];

const PAGE_SIZE = 20;

export default function CrawlStatusPage() {
  const { t, lang } = useI18n();
  const LOG_COLUMNS = lang === 'zh' ? LOG_COLUMNS_ZH : LOG_COLUMNS_EN;
  const [page, setPage] = useState(1);
  const [sourceFilter, setSourceFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortKey, setSortKey] = useState('started_at');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const sortParam = useMemo(() => {
    if (!sortKey) return undefined;
    return sortDir === 'desc' ? `-${sortKey}` : sortKey;
  }, [sortKey, sortDir]);

  const logParams = useMemo(
    () => ({
      page,
      page_size: PAGE_SIZE,
      source: sourceFilter || undefined,
      status: statusFilter || undefined,
      sort: sortParam,
    }),
    [page, sourceFilter, statusFilter, sortParam],
  );

  const { logs, jobs, totalLogs, loading, error, triggerCrawl } = useCrawlStatus(logParams);

  const totalPages = Math.max(1, Math.ceil(totalLogs / PAGE_SIZE));

  const [triggering, setTriggering] = useState<string | null>(null);
  const [triggerMsg, setTriggerMsg] = useState('');

  function handleSort(key: string) {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
    setPage(1);
  }

  async function handleTrigger(source: string) {
    setTriggering(source);
    setTriggerMsg('');
    try {
      const msg = await triggerCrawl(source);
      setTriggerMsg(msg);
    } catch (err) {
      setTriggerMsg((err as Error).message || 'Failed to trigger crawl');
    } finally {
      setTriggering(null);
    }
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t('crawls.title')}</h1>

      {/* Scheduler Status Cards */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-[var(--text-primary)]">{t('crawls.scheduler')}</h2>
        {loading && !jobs.length && <LoadingSkeleton variant="text" rows={4} />}
        {!loading && jobs.length === 0 && (
          <p className="text-sm text-[var(--text-tertiary)]">{t('crawls.noJobs')}</p>
        )}
        {!loading && jobs.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            {jobs.map((job) => (
              <div key={job.source} className="glass-card p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-[var(--text-primary)] capitalize">{t('crawls.job_' + job.source.replace('_', ''))}</h3>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                    job.enabled ? 'bg-green-100 text-green-700' : 'bg-white/15 text-[var(--text-secondary)]'
                  }`}>
                    {job.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  {job.interval_minutes && (
                    <div>
                      <p className="text-[var(--text-secondary)]">{t('crawls.interval')}</p>
                      <p className="font-medium text-[var(--text-primary)]">{t('crawls.every', {min: job.interval_minutes})}</p>
                    </div>
                  )}
                  {job.cron && (
                    <div>
                      <p className="text-[var(--text-secondary)]">{t('crawls.cron')}</p>
                      <p className="font-medium text-[var(--text-primary)]">{job.cron}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-[var(--text-secondary)]">{t('crawls.lastRun')}</p>
                    <p className="font-medium text-[var(--text-primary)]">
                      {job.last_run ? new Date(job.last_run).toLocaleString() : t('crawls.never')}
                    </p>
                  </div>
                  <div>
                    <p className="text-[var(--text-secondary)]">{t('crawls.nextRun')}</p>
                    <p className="font-medium text-[var(--text-primary)]">
                      {job.next_run ? new Date(job.next_run).toLocaleString() : t('crawls.notScheduled')}
                    </p>
                  </div>
                  <div>
                    <p className="text-[var(--text-secondary)]">{t('crawls.lastStatus')}</p>
                    {job.last_status ? (
                      <StatusBadge status={job.last_status} />
                    ) : (
                      <span className="text-[var(--text-tertiary)]">{t('crawls.na')}</span>
                    )}
                  </div>
                </div>
                {(job.source === 'crawl_arxiv' || job.source === 'crawl_github') && (() => {
                  const triggerSource = job.source.replace('crawl_', '');
                  return (
                    <button
                      type="button"
                      onClick={() => handleTrigger(triggerSource)}
                      disabled={triggering === triggerSource}
                      className="mt-3 w-full glass-btn glass-btn-primary glass-btn-sm w-full"
                    >
                      {triggering === triggerSource ? t('crawls.triggering') : t('crawls.triggerBtn')}
                    </button>
                  );
                })()}
              </div>
            ))}
          </div>
        )}
        {triggerMsg && (
          <p className={`mt-2 text-sm ${triggerMsg.includes('failed') || triggerMsg.includes('already running') ? 'text-red-600' : 'text-green-600'}`}>
            {triggerMsg}
          </p>
        )}
      </section>

      {/* Crawl Logs */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">{t('crawls.logs')}</h2>
          <div className="flex items-center gap-3">
            <GlassDropdown
              value={sourceFilter}
              options={[{ value: '', label: t('crawls.allSources') }, { value: 'arxiv', label: 'arxiv' }, { value: 'github', label: 'github' }]}
              onChange={(v) => { setSourceFilter(v); setPage(1); }}
              className="min-w-[140px]"
            />
            <GlassDropdown
              value={statusFilter}
              options={[{ value: '', label: t('crawls.allStatus') }, { value: 'success', label: 'success' }, { value: 'partial', label: 'partial' }, { value: 'failed', label: 'failed' }, { value: 'running', label: 'running' }]}
              onChange={(v) => { setStatusFilter(v); setPage(1); }}
              className="min-w-[140px]"
            />
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
        )}

        {loading && <LoadingSkeleton variant="table-row" rows={6} />}

        {!loading && !error && logs.length === 0 && (
          <div className="glass-panel p-12 text-center">
            <p className="text-[var(--text-secondary)]">{t('crawls.noLogs')}</p>
          </div>
        )}

        {!loading && logs.length > 0 && (
          <>
            <SortableTable
              columns={LOG_COLUMNS}
              sortKey={sortKey}
              sortDir={sortDir}
              onSort={handleSort}
            >
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-white/20">
                  <td className="px-4 py-3">
                    <span className="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 capitalize">
                      {log.source}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[var(--text-primary)]">
                    {new Date(log.started_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-[var(--text-primary)]">
                    {log.finished_at ? new Date(log.finished_at).toLocaleString() : '--'}
                  </td>
                  <td className="px-4 py-3 font-medium text-[var(--text-primary)]">{log.items_found}</td>
                  <td className="px-4 py-3 font-medium text-green-700">{log.items_new}</td>
                  <td className="px-4 py-3 font-medium text-blue-700">{log.items_updated}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={log.status} />
                  </td>
                  <td className="px-4 py-3 max-w-xs truncate text-[var(--text-secondary)]">
                    {log.error_message || '--'}
                  </td>
                </tr>
              ))}
            </SortableTable>
            <Pagination page={page} pages={totalPages} total={totalLogs} onPageChange={setPage} />
          </>
        )}
      </section>
    </div>
  );
}
