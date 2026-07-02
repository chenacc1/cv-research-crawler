import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { usePapers } from '../hooks/usePapers';
import { useTags } from '../hooks/useTags';
import { useDebounce } from '../hooks/useDebounce';
import type { PaperQueryParams } from '../types/paper';
import FilterBar from '../components/shared/FilterBar';
import type { ActiveFilter } from '../components/shared/FilterBar';
import Pagination from '../components/shared/Pagination';
import TagBadge from '../components/shared/TagBadge';
import TagSelector from '../components/shared/TagSelector';
import DateRangePicker from '../components/shared/DateRangePicker';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import GlassDropdown from '../components/shared/GlassDropdown';
import { useI18n } from '../i18n/I18nProvider';

const SOURCES = ['arxiv', 'dblp', 'openreview'];

export default function PaperListPage() {
  const [page, setPage] = useState(1);
  const [source, setSource] = useState<string[]>([]);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [sort, setSort] = useState('-published_date');
  const [venue, setVenue] = useState('');

  const debouncedSearch = useDebounce(searchInput, 300);

  const params: PaperQueryParams = useMemo(
    () => ({
      page,
      page_size: 20,
      source: source.length ? source : undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      q: debouncedSearch || undefined,
      tag_id: selectedTagIds.length ? selectedTagIds : undefined,
      sort,
      venue: venue || undefined,
    }),
    [page, source, dateFrom, dateTo, debouncedSearch, selectedTagIds, sort, venue],
  );

  const { papers, total, pages, loading, error } = usePapers(params);
  const { tags } = useTags();
  const { t, lang, toggleLang } = useI18n();

  const SORT_OPTIONS = [
    { value: '-published_date', label: t('papers.sortNewest') },
    { value: 'published_date', label: t('papers.sortOldest') },
    { value: '-crawled_at', label: t('papers.sortCrawled') },
    { value: 'title', label: t('papers.sortTitle') },
  ];

  const activeFilters: ActiveFilter[] = [
    ...source.map((s) => ({ label: 'Source', value: s, onRemove: () => setSource(source.filter((v) => v !== s)) })),
    ...(dateFrom ? [{ label: 'From', value: dateFrom, onRemove: () => setDateFrom('') }] : []),
    ...(dateTo ? [{ label: 'To', value: dateTo, onRemove: () => setDateTo('') }] : []),
    ...selectedTagIds.map((tid) => {
      const t = tags.find((tg) => tg.id === tid);
      return { label: 'Tag', value: t?.name || tid, onRemove: () => setSelectedTagIds(selectedTagIds.filter((id) => id !== tid)) };
    }),
    ...(venue ? [{ label: 'Venue', value: venue, onRemove: () => setVenue('') }] : []),
    ...(debouncedSearch ? [{ label: 'Search', value: debouncedSearch, onRemove: () => setSearchInput('') }] : []),
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t('papers.title')}</h1>
        <button
          type="button"
          onClick={toggleLang}
          className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
            lang === 'zh' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
          }`}
        >
          {t('shared.langBtn')}
        </button>
      </div>

      <FilterBar filters={activeFilters}>
        <GlassDropdown
          options={SOURCES.map((s) => ({ value: s, label: s }))}
          value=""
          multiple
          selectedValues={source}
          onMultiChange={(vals) => { setSource(vals); setPage(1); }}
          placeholder="Source"
          className="min-w-[140px]"
        />

        <DateRangePicker
          dateFrom={dateFrom}
          dateTo={dateTo}
          onDateFromChange={(v) => { setDateFrom(v); setPage(1); }}
          onDateToChange={(v) => { setDateTo(v); setPage(1); }}
          onClear={() => { setDateFrom(''); setDateTo(''); setPage(1); }}
        />

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
          placeholder="Search title & abstract..."
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

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && <LoadingSkeleton variant="card" rows={6} />}

      {/* Empty state */}
      {!loading && !error && papers.length === 0 && (
        <div className="glass-panel p-12 text-center">
          <p className="text-[var(--text-secondary)]">{t('papers.noMatch')}</p>
        </div>
      )}

      {/* Paper cards */}
      {!loading && papers.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {papers.map((paper) => (
              <Link
                key={paper.id}
                to={`/papers/${paper.id}`}
                className="glass-card block p-4 transition-all hover:translate-y-[-2px]"
              >
                <h3 className="mb-1 line-clamp-2 text-sm font-semibold text-[var(--text-primary)]">
                  {paper.title}
                </h3>
                <p className="mb-2 text-xs text-[var(--text-secondary)]">
                  {paper.author_names.slice(0, 3).join(', ')}
                  {paper.author_names.length > 3 && ` +${paper.author_names.length - 3} more`}
                </p>
                {(lang === 'zh' ? paper.summary_cn : paper.summary_en) && (
                  <p className={`mb-1 line-clamp-2 rounded p-1.5 text-xs ${lang === 'zh' ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'}`}>
                    <span className="font-medium">{lang === 'zh' ? 'AI: ' : 'AI: '}</span>
                    {lang === 'zh' ? paper.summary_cn : paper.summary_en}
                  </p>
                )}
                <div className="mb-2 flex flex-wrap items-center gap-1.5">
                  <span className="inline-flex items-center rounded-md bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-700">
                    {paper.source}
                  </span>
                  {paper.venue && (
                    <span className="inline-flex items-center rounded-md bg-purple-50 px-1.5 py-0.5 text-xs font-medium text-purple-700">
                      {paper.venue}
                    </span>
                  )}
                </div>
                <div className="mb-2 flex flex-wrap gap-1">
                  {paper.categories.slice(0, 3).map((cat) => (
                    <span key={cat.id} className="rounded-full bg-white/15 px-1.5 py-0.5 text-xs text-[var(--text-secondary)]">
                      {cat.name}
                    </span>
                  ))}
                  {paper.categories.length > 3 && (
                    <span className="text-xs text-[var(--text-tertiary)]">+{paper.categories.length - 3}</span>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-1">
                  {paper.tags.map((tag) => (
                    <TagBadge key={tag.id} tag={tag} size="sm" />
                  ))}
                </div>
                <div className="mt-2 flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
                  {paper.published_date && <span>{paper.published_date}</span>}
                  {paper.code_url && (
                    <a
                      href={paper.code_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-blue-500 hover:underline"
                    >
                      Code
                    </a>
                  )}
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
