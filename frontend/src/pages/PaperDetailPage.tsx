import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getPaper, setPaperTags } from '../api/papers';
import { useTags } from '../hooks/useTags';
import type { PaperDetail } from '../types/paper';
import TagBadge from '../components/shared/TagBadge';
import TagSelector from '../components/shared/TagSelector';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import { useI18n } from '../i18n/I18nProvider';

export default function PaperDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [paper, setPaper] = useState<PaperDetail | null>(null);
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
    getPaper(id)
      .then((data) => { if (!cancelled) setPaper(data); })
      .catch((err: Error) => { if (!cancelled) setError(err.message || 'Failed to load paper'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  async function handleTagsChange(tagIds: string[]) {
    if (!id) return;
    setSaving(true);
    try {
      const res = await setPaperTags(id, tagIds);
      setPaper((prev) => prev ? { ...prev, tags: res.tags } : prev);
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

  if (!paper) return null;

  return (
    <div className="space-y-6">
      {/* Back link */}
      <button
        type="button"
        onClick={() => navigate('/papers')}
        className="text-sm text-blue-600 hover:underline"
      >
        &larr; {t('papers.backToList')}
      </button>

      {/* Title & metadata */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">{paper.title}</h1>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
            {paper.source}
          </span>
          {paper.venue && (
            <span className="rounded-md bg-purple-50 px-2 py-0.5 text-xs font-medium text-purple-700">
              {paper.venue}
            </span>
          )}
          {paper.published_date && (
            <span className="text-sm text-[var(--text-secondary)]">{paper.published_date}</span>
          )}
        </div>
      </div>

      {/* External links */}
      <div className="flex flex-wrap gap-2">
        <a
          href={paper.url}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md bg-white/15 px-3 py-1.5 text-sm font-medium text-[var(--text-primary)] hover:bg-white/20"
        >
          {t('papers.viewPaper')}
        </a>
        {paper.pdf_url && (
          <a
            href={paper.pdf_url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md bg-red-50 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100"
          >
            PDF
          </a>
        )}
        {paper.code_url && (
          <a
            href={paper.code_url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md bg-green-50 px-3 py-1.5 text-sm font-medium text-green-700 hover:bg-green-100"
          >
            Code
          </a>
        )}
      </div>

      {/* AI Summary */}
      {(paper.summary_cn || paper.summary_en) && (
        <div>
          <h2 className="mb-2 text-lg font-semibold text-[var(--text-primary)] flex items-center gap-2">
            {t('papers.aiSummary')}
            <button
              type="button"
              onClick={toggleLang}
              className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
                lang === 'zh' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'
              }`}
            >
              {lang === 'zh' ? t('shared.lang') : 'English'}
            </button>
          </h2>
          <div className={`rounded-lg border p-4 ${lang === 'zh' ? 'border-blue-200 bg-blue-50' : 'border-green-200 bg-green-50'}`}>
            <p className="whitespace-pre-line text-sm leading-relaxed text-[var(--text-primary)]">
              {lang === 'zh' ? (paper.summary_cn || paper.summary_en) : (paper.summary_en || paper.summary_cn)}
            </p>
          </div>
        </div>
      )}

      {/* Abstract */}
      <div>
        <h2 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">Abstract</h2>
        <p className="whitespace-pre-line text-sm leading-relaxed text-[var(--text-primary)]">
          {paper.abstract || 'No abstract available.'}
        </p>
      </div>

      {/* Authors */}
      <div>
        <h2 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">Authors</h2>
        <ul className="space-y-1">
          {paper.authors.map((author) => (
            <li key={author.id} className="text-sm text-[var(--text-primary)]">
              <span className="font-medium">{author.name}</span>
              {author.affiliation && (
                <span className="text-[var(--text-secondary)]"> -- {author.affiliation}</span>
              )}
            </li>
          ))}
        </ul>
      </div>

      {/* Categories */}
      <div>
        <h2 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">Categories</h2>
        <div className="flex flex-wrap gap-1.5">
          {paper.categories.map((cat) => (
            <span key={cat.id} className="rounded-full bg-white/15 px-2 py-0.5 text-sm text-[var(--text-primary)]">
              {cat.name}
            </span>
          ))}
        </div>
      </div>

      {/* User Tags */}
      <div>
        <h2 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">Tags</h2>
        <div className="flex flex-wrap items-center gap-2">
          {paper.tags.map((tag) => (
            <TagBadge key={tag.id} tag={tag} />
          ))}
        </div>
        <div className="mt-3 max-w-xs">
          <TagSelector
            availableTags={tags}
            selectedTagIds={paper.tags.map((t) => t.id)}
            onChange={handleTagsChange}
            placeholder={saving ? 'Saving...' : 'Manage tags'}
          />
        </div>
      </div>

      {/* Versions */}
      {paper.versions && paper.versions.length > 0 && (
        <div>
          <h2 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">Versions</h2>
          <ul className="space-y-1">
            {paper.versions.map((v) => (
              <li key={v.id} className="text-sm">
                <Link to={`/papers/${v.id}`} className="text-blue-600 hover:underline">
                  {v.title}
                </Link>
                <span className="ml-2 text-xs text-[var(--text-tertiary)]">({v.source})</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Merged info */}
      {paper.merged_into_id && (
        <div className="rounded-lg bg-yellow-50 p-3 text-sm text-yellow-800">
          This paper has been merged into{' '}
          <Link to={`/papers/${paper.merged_into_id}`} className="underline">
            another version
          </Link>.
        </div>
      )}
    </div>
  );
}
