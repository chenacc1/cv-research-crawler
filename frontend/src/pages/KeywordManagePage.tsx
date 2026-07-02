import { useState, useEffect, useCallback } from 'react';
import { listKeywords, expandKeywords, batchAddKeywords, toggleKeyword, deleteKeyword } from '../api/crawlKeywords';
import type { CrawlKeyword } from '../types/keyword';
import { useI18n } from '../i18n/I18nProvider';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';

export default function KeywordManagePage() {
  const { t } = useI18n();
  const [keywords, setKeywords] = useState<CrawlKeyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [topic, setTopic] = useState('');
  const [expanding, setExpanding] = useState(false);
  const [expandedKeywords, setExpandedKeywords] = useState<string[]>([]);
  const [selectedNew, setSelectedNew] = useState<Set<string>>(new Set());
  const [expandError, setExpandError] = useState('');

  const load = useCallback(async () => {
    try { const items = await listKeywords(); setKeywords(items); }
    catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  async function handleExpand() {
    if (!topic.trim()) return;
    setExpanding(true); setExpandError(''); setSelectedNew(new Set());
    try { const kws = await expandKeywords(topic.trim()); setExpandedKeywords(kws); setSelectedNew(new Set(kws)); }
    catch (e) { setExpandError((e as Error).message || 'Expansion failed'); }
    finally { setExpanding(false); }
  }

  function toggleNew(kw: string) {
    setSelectedNew((prev) => { const next = new Set(prev); if (next.has(kw)) next.delete(kw); else next.add(kw); return next; });
  }

  async function handleApply() {
    const toAdd = [...selectedNew];
    if (!toAdd.length) return;
    try { const items = await batchAddKeywords(toAdd); setKeywords(items); setExpandedKeywords([]); setSelectedNew(new Set()); setTopic(''); }
    catch (e) { setExpandError((e as Error).message || 'Failed to apply'); }
  }

  async function handleToggle(kw: CrawlKeyword) {
    try { const updated = await toggleKeyword(kw.id, !kw.enabled); setKeywords((prev) => prev.map((k) => (k.id === kw.id ? updated : k))); } catch { /* ignore */ }
  }

  async function handleDelete(kw: CrawlKeyword) {
    try { await deleteKeyword(kw.id); setKeywords((prev) => prev.filter((k) => k.id !== kw.id)); } catch { /* ignore */ }
  }

  const enabledCount = keywords.filter((k) => k.enabled).length;

  if (loading) return <LoadingSkeleton variant="card" rows={6} />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{t('kw.title')}</h1>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      <div className="glass-panel p-4">
        <h2 className="mb-3 text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{t('kw.expand')}</h2>
        <p className="mb-3 text-sm" style={{ color: 'var(--text-secondary)' }}>{t('kw.expandDesc')}</p>
        <div className="flex flex-wrap items-center gap-3">
          <input type="text" value={topic} onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleExpand(); }}
            placeholder="e.g. 3D computer vision, image generation..."
            className="glass-input flex-1" />
          <button type="button" onClick={handleExpand} disabled={expanding || !topic.trim()}
            className="glass-btn glass-btn-primary">
            {expanding ? t('kw.expanding') : t('kw.expandBtn')}
          </button>
        </div>
        {expandError && <p className="mt-2 text-sm text-red-600">{expandError}</p>}

        {expandedKeywords.length > 0 && (
          <div className="mt-4">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                {t('kw.generated')} ({selectedNew.size}/{expandedKeywords.length} {t('kw.selected')})
              </p>
              <div className="flex gap-2">
                <button onClick={() => setSelectedNew(new Set(expandedKeywords))} className="text-xs text-blue-600 hover:underline">{t('kw.selectAll')}</button>
                <button onClick={() => setSelectedNew(new Set())} className="text-xs hover:underline" style={{ color: 'var(--text-secondary)' }}>{t('kw.deselectAll')}</button>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {expandedKeywords.map((kw) => (
                <label key={kw}
                  className={`glass-tag cursor-pointer px-3 py-1 text-sm ${selectedNew.has(kw) ? 'glass-tag-blue' : ''}`}
                  style={selectedNew.has(kw) ? {} : { background: 'rgba(0,0,0,0.04)', color: 'var(--text-secondary)' }}>
                  <input type="checkbox" checked={selectedNew.has(kw)} onChange={() => toggleNew(kw)} className="sr-only" />
                  {kw}
                </label>
              ))}
            </div>
            <button type="button" onClick={handleApply} disabled={selectedNew.size === 0}
              className="glass-btn glass-btn-primary mt-3">
              {t('kw.apply')} ({selectedNew.size})
            </button>
          </div>
        )}
      </div>

      <div className="glass-panel">
        <div className="px-4 py-3" style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
              {t('kw.activeKeywords')} ({enabledCount}/{keywords.length} {t('kw.enabled')})
            </h2>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{t('kw.onlyEnabled')}</span>
          </div>
        </div>

        {keywords.length === 0 ? (
          <div className="p-12 text-center text-sm" style={{ color: 'var(--text-tertiary)' }}>{t('kw.noKeywords')}</div>
        ) : (
          <div className="divide-y" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
            {keywords.map((kw) => (
              <div key={kw.id} className="flex items-center justify-between px-4 py-3" style={{ transition: 'background 0.15s' }}>
                <div className="flex items-center gap-3">
                  <label className="glass-toggle">
                    <input type="checkbox" checked={kw.enabled} onChange={() => handleToggle(kw)} />
                    <div className="glass-toggle-track"><div className="glass-toggle-thumb" /></div>
                  </label>
                  <span className="text-sm" style={{ color: kw.enabled ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>{kw.keyword}</span>
                </div>
                <button onClick={() => handleDelete(kw)} className="text-xs text-red-500 hover:underline">{t('kw.delete')}</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
