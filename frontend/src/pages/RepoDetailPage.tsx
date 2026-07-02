import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getRepo, setRepoTags } from '../api/repos';
import { useTags } from '../hooks/useTags';
import type { RepoDetail } from '../types/repo';
import TagBadge from '../components/shared/TagBadge';
import TagSelector from '../components/shared/TagSelector';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import { useI18n } from '../i18n/I18nProvider';

export default function RepoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [repo, setRepo] = useState<RepoDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const { tags } = useTags();
  const { t, lang, toggleLang } = useI18n();

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    getRepo(id)
      .then((data) => { if (!cancelled) setRepo(data); })
      .catch((err: Error) => { if (!cancelled) setError(err.message || 'Failed to load repo'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  async function handleTagsChange(tagIds: string[]) {
    if (!id) return;
    setSaving(true);
    try {
      const res = await setRepoTags(id, tagIds);
      setRepo((prev) => prev ? { ...prev, tags: res.tags } : prev);
    } catch (err) {
      setError((err as Error).message || 'Failed to update tags');
    } finally {
      setSaving(false);
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

  if (!repo) return null;

  return (
    <div className="space-y-6">
      <button
        type="button"
        onClick={() => navigate('/repos')}
        className="text-sm text-blue-600 hover:underline"
      >
        &larr; Back to Repos
      </button>

      <div>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">{repo.full_name}</h1>
            {repo.description && (
              <p className="mt-2 text-[var(--text-secondary)]">{repo.description}</p>
            )}
          </div>
          <a
            href={repo.url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 rounded-md bg-gray-800 px-4 py-2 text-sm font-medium text-white hover:bg-gray-900"
          >
            View on GitHub
          </a>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Stars" value={repo.stars.toLocaleString()} />
        <Stat label="Forks" value={repo.forks.toLocaleString()} />
        {repo.language && <Stat label="Language" value={repo.language} />}
        {repo.pushed_at && (
          <Stat label="Last Pushed" value={new Date(repo.pushed_at).toLocaleDateString()} />
        )}
      </div>

      {/* Crawl info */}
      <div className="text-xs text-[var(--text-tertiary)]">
        Crawled: {new Date(repo.crawled_at).toLocaleString()}
        {repo.last_crawled_at !== repo.crawled_at && (
          <> | Last recrawled: {new Date(repo.last_crawled_at).toLocaleString()}</>
        )}
      </div>

      {/* AI Summary */}
      {(repo.summary_cn || repo.summary_en) && (
        <div>
          <h2 className="mb-2 text-lg font-semibold text-[var(--text-primary)] flex items-center gap-2">
            AI 总结
            <button
              type="button"
              onClick={toggleLang}
              className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
                lang === 'zh' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'
              }`}
            >
              {lang === 'zh' ? '中文' : 'English'}
            </button>
          </h2>
          <div className={`rounded-lg border p-4 ${lang === 'zh' ? 'border-blue-200 bg-blue-50' : 'border-green-200 bg-green-50'}`}>
            <p className="whitespace-pre-line text-sm leading-relaxed text-[var(--text-primary)]">
              {lang === 'zh' ? (repo.summary_cn || repo.summary_en) : (repo.summary_en || repo.summary_cn)}
            </p>
          </div>
        </div>
      )}

      {/* Topics */}
      <div>
        <h2 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">Topics</h2>
        <div className="flex flex-wrap gap-1.5">
          {repo.topics.map((topic) => (
            <span key={topic} className="rounded-full bg-blue-50 px-2 py-0.5 text-sm text-blue-700">
              {topic}
            </span>
          ))}
          {repo.topics.length === 0 && (
            <span className="text-sm text-[var(--text-tertiary)]">{t('repos.noTopics')}</span>
          )}
        </div>
      </div>

      {/* User Tags */}
      <div>
        <h2 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">Tags</h2>
        <div className="mb-3 flex flex-wrap gap-2">
          {repo.tags.map((tag) => (
            <TagBadge key={tag.id} tag={tag} />
          ))}
        </div>
        <div className="max-w-xs">
          <TagSelector
            availableTags={tags}
            selectedTagIds={repo.tags.map((t) => t.id)}
            onChange={handleTagsChange}
            placeholder={saving ? 'Saving...' : 'Manage tags'}
          />
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg glass-panel p-3">
      <p className="text-xs font-medium text-[var(--text-secondary)]">{label}</p>
      <p className="mt-0.5 text-lg font-semibold text-[var(--text-primary)]">{value}</p>
    </div>
  );
}
