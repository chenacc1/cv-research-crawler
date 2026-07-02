import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useRepos } from '../hooks/useRepos';
import { useTags } from '../hooks/useTags';
import { useDebounce } from '../hooks/useDebounce';
import type { RepoQueryParams } from '../types/repo';
import FilterBar from '../components/shared/FilterBar';
import type { ActiveFilter } from '../components/shared/FilterBar';
import Pagination from '../components/shared/Pagination';
import TagBadge from '../components/shared/TagBadge';
import TagSelector from '../components/shared/TagSelector';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import { useI18n } from '../i18n/I18nProvider';
import GlassDropdown from '../components/shared/GlassDropdown';

const LANGUAGES = ['Python', 'JavaScript', 'TypeScript', 'Rust', 'Go', 'Java', 'C++', 'C', 'Jupyter Notebook', 'Shell'];

export default function RepoListPage() {
  const [page, setPage] = useState(1);
  const [language, setLanguage] = useState<string[]>([]);
  const [searchInput, setSearchInput] = useState('');
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [sort, setSort] = useState('-stars');
  const [starsMin, setStarsMin] = useState('');
  const [starsMax, setStarsMax] = useState('');

  const debouncedSearch = useDebounce(searchInput, 300);

  const params: RepoQueryParams = useMemo(
    () => ({
      page,
      page_size: 20,
      language: language.length ? language : undefined,
      q: debouncedSearch || undefined,
      tag_id: selectedTagIds.length ? selectedTagIds : undefined,
      sort,
      stars_min: starsMin ? Number(starsMin) : undefined,
      stars_max: starsMax ? Number(starsMax) : undefined,
    }),
    [page, language, debouncedSearch, selectedTagIds, sort, starsMin, starsMax],
  );

  const { repos, total, pages, loading, error } = useRepos(params);
  const { tags } = useTags();
  const { t, lang, toggleLang } = useI18n();

  const SORT_OPTIONS = [
    { value: '-stars', label: t('repos.sortStars') },
    { value: '-forks', label: t('repos.sortForks') },
    { value: '-pushed_at', label: t('repos.sortPushed') },
    { value: '-crawled_at', label: t('repos.sortCrawled') },
  ];

  const activeFilters: ActiveFilter[] = [
    ...language.map((l) => ({ label: 'Language', value: l, onRemove: () => setLanguage(language.filter((v) => v !== l)) })),
    ...selectedTagIds.map((tid) => {
      const t = tags.find((tg) => tg.id === tid);
      return { label: 'Tag', value: t?.name || tid, onRemove: () => setSelectedTagIds(selectedTagIds.filter((id) => id !== tid)) };
    }),
    ...(starsMin ? [{ label: 'Stars min', value: starsMin, onRemove: () => setStarsMin('') }] : []),
    ...(starsMax ? [{ label: 'Stars max', value: starsMax, onRemove: () => setStarsMax('') }] : []),
    ...(debouncedSearch ? [{ label: 'Search', value: debouncedSearch, onRemove: () => setSearchInput('') }] : []),
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t('repos.title')}</h1>
        <button
          type="button"
          onClick={toggleLang}
          className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
            lang === 'zh' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
          }`}
        >
          {lang === 'zh' ? '中文' : 'English'}
        </button>
      </div>

      <FilterBar filters={activeFilters}>
        <GlassDropdown
          options={LANGUAGES.map((l) => ({ value: l, label: l }))}
          value=""
          multiple
          selectedValues={language}
          onMultiChange={(vals) => { setLanguage(vals); setPage(1); }}
          placeholder="Language"
          className="min-w-[150px]"
        />

        <div className="flex items-center gap-1">
          <input
            type="number"
            placeholder="Min stars"
            value={starsMin}
            onChange={(e) => { setStarsMin(e.target.value); setPage(1); }}
            className="w-24 glass-input h-[34px] px-2 text-sm"
          />
          <span className="text-[var(--text-tertiary)]">-</span>
          <input
            type="number"
            placeholder="Max stars"
            value={starsMax}
            onChange={(e) => { setStarsMax(e.target.value); setPage(1); }}
            className="w-24 glass-input h-[34px] px-2 text-sm"
          />
        </div>

        <div className="w-48">
          <TagSelector
            availableTags={tags}
            selectedTagIds={selectedTagIds}
            onChange={(ids) => { setSelectedTagIds(ids); setPage(1); }}
            placeholder="Filter by tags..."
          />
        </div>

        <input
          type="text"
          placeholder="Search name & description..."
          value={searchInput}
          onChange={(e) => { setSearchInput(e.target.value); setPage(1); }}
          className="glass-input text-sm"
        />

        <GlassDropdown
          value={sort}
          options={SORT_OPTIONS}
          onChange={(v) => { setSort(v); setPage(1); }}
          className="min-w-[170px]"
        />
      </FilterBar>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      {loading && <LoadingSkeleton variant="card" rows={6} />}

      {!loading && !error && repos.length === 0 && (
        <div className="glass-panel p-12 text-center">
          <p className="text-[var(--text-secondary)]">{t('repos.noMatch')}</p>
        </div>
      )}

      {!loading && repos.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {repos.map((repo) => (
              <Link
                key={repo.id}
                to={`/repos/${repo.id}`}
                className="block glass-card p-4 transition-all hover:translate-y-[-2px]"
              >
                <div className="mb-2 flex items-start justify-between gap-2">
                  <h3 className="line-clamp-1 text-sm font-semibold text-[var(--text-primary)]">
                    {repo.full_name}
                  </h3>
                  <a
                    href={repo.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="shrink-0 text-xs text-blue-500 hover:underline"
                  >
                    GitHub
                  </a>
                </div>
                {repo.description && (
                  <p className="mb-3 line-clamp-2 text-xs text-[var(--text-secondary)]">{repo.description}</p>
                )}
                {(lang === 'zh' ? repo.summary_cn : repo.summary_en) && (
                  <p className={`mb-1 line-clamp-2 rounded p-1.5 text-xs ${lang === 'zh' ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'}`}>
                    <span className="font-medium">AI: </span>
                    {lang === 'zh' ? repo.summary_cn : repo.summary_en}
                  </p>
                )}
                <div className="mb-2 flex items-center gap-3 text-xs text-[var(--text-secondary)]">
                  <span title="Stars">{repo.stars.toLocaleString()} stars</span>
                  <span title="Forks">{repo.forks.toLocaleString()} forks</span>
                  {repo.language && (
                    <span className="rounded bg-white/15 px-1.5 py-0.5 font-medium text-[var(--text-primary)]">
                      {repo.language}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1">
                  {repo.topics.slice(0, 3).map((topic) => (
                    <span key={topic} className="rounded-full bg-blue-50 px-1.5 py-0.5 text-xs text-blue-600">
                      {topic}
                    </span>
                  ))}
                  {repo.topics.length > 3 && (
                    <span className="text-xs text-[var(--text-tertiary)]">+{repo.topics.length - 3}</span>
                  )}
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {repo.tags.map((tag) => (
                    <TagBadge key={tag.id} tag={tag} size="sm" />
                  ))}
                </div>
              </Link>
            ))}
          </div>
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
