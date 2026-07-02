import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getStats } from '../api/stats';
import type { StatsResponse } from '../types/stats';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import { useI18n } from '../i18n/I18nProvider';

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t } = useI18n();

  useEffect(() => {
    let cancelled = false;
    getStats()
      .then((data) => { if (!cancelled) setStats(data); })
      .catch((err: Error) => { if (!cancelled) setError(err.message || 'Failed to load stats'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  if (loading) return <LoadingSkeleton variant="card" rows={6} />;
  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-red-700">{error}</p>
      </div>
    );
  }
  if (!stats) return null;

  const cards = [
    { label: t('dashboard.totalPapers'), value: stats.papers.total.toLocaleString(), color: 'text-blue-600' },
    { label: t('dashboard.papersToday'), value: stats.papers.new_today.toLocaleString(), color: 'text-green-600' },
    { label: t('dashboard.papersWeek'), value: stats.papers.new_this_week.toLocaleString(), color: 'text-emerald-600' },
    { label: t('dashboard.totalRepos'), value: stats.repos.total.toLocaleString(), color: 'text-purple-600' },
    { label: t('dashboard.reposToday'), value: stats.repos.new_today.toLocaleString(), color: 'text-indigo-600' },
    { label: t('dashboard.totalTags'), value: stats.tags.total.toLocaleString(), color: 'text-orange-600' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t('dashboard.title')}</h1>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => (
          <div key={card.label} className="glass-card p-4">
            <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>{card.label}</p>
            <p className="mt-1 text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* Crawl info */}
      <div className="glass-card p-4">
        <h2 className="mb-3 text-lg font-semibold text-[var(--text-primary)]">{t('dashboard.crawlStatus')}</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-sm text-[var(--text-secondary)]">{t('dashboard.lastArxiv')}</p>
            <p className="font-medium text-[var(--text-primary)]">
              {stats.crawls.last_arxiv ? new Date(stats.crawls.last_arxiv).toLocaleString() : 'Never'}
            </p>
          </div>
          <div>
            <p className="text-sm text-[var(--text-secondary)]">{t('dashboard.lastGithub')}</p>
            <p className="font-medium text-[var(--text-primary)]">
              {stats.crawls.last_github ? new Date(stats.crawls.last_github).toLocaleString() : t('crawls.never')}
            </p>
          </div>
          <div>
            <p className="text-sm text-[var(--text-secondary)]">{t('dashboard.totalRuns')}</p>
            <p className="font-medium text-[var(--text-primary)]">{stats.crawls.total_runs.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-[var(--text-secondary)]">{t('dashboard.successRate')}</p>
            <p className="font-medium text-[var(--text-primary)]">{(stats.crawls.success_rate * 100).toFixed(1)}%</p>
          </div>
        </div>
      </div>

      {/* Reports summary */}
      <div className="glass-card p-4">
        <h2 className="mb-3 text-lg font-semibold text-[var(--text-primary)]">{t('dashboard.reports')}</h2>
        <p className="text-sm text-[var(--text-secondary)]">
          {t('dashboard.reportSummary', { daily: stats.reports.daily_count, weekly: stats.reports.weekly_count })}
        </p>
      </div>

      {/* Top categories & languages */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="glass-card p-4">
          <h2 className="mb-3 text-lg font-semibold text-[var(--text-primary)]">{t('dashboard.topCategories')}</h2>
          <ul className="space-y-2">
            {stats.top_categories.map((cat) => (
              <li key={cat.name} className="flex justify-between text-sm">
                <span className="text-[var(--text-primary)]">{cat.name}</span>
                <span className="font-medium text-[var(--text-primary)]">{cat.paper_count.toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="glass-card p-4">
          <h2 className="mb-3 text-lg font-semibold text-[var(--text-primary)]">{t('dashboard.topLanguages')}</h2>
          <ul className="space-y-2">
            {stats.top_languages.map((lang) => (
              <li key={lang.language} className="flex justify-between text-sm">
                <span className="text-[var(--text-primary)]">{lang.language}</span>
                <span className="font-medium text-[var(--text-primary)]">{lang.repo_count.toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Quick links */}
      <div className="flex flex-wrap gap-3">
        <Link to="/papers" className="glass-btn glass-btn-primary">{t('dashboard.browsePapers')}</Link>
        <Link to="/repos" className="glass-btn glass-btn-primary">{t('dashboard.browseRepos')}</Link>
        <Link to="/reports" className="glass-btn glass-btn-primary">{t('dashboard.viewReports')}</Link>
        <Link to="/crawls" className="glass-btn glass-btn-primary">{t('dashboard.crawlStatus2')}</Link>
      </div>
    </div>
  );
}
