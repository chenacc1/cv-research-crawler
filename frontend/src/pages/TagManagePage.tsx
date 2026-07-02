import { useState } from 'react';
import { useTags } from '../hooks/useTags';
import type { TagDetail } from '../types/tag';
import { tagBadgeStyle } from '../components/shared/TagBadge';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import { useI18n } from '../i18n/I18nProvider';

const COLOR_PALETTE = [
  '#EF4444', '#F97316', '#F59E0B', '#EAB308',
  '#84CC16', '#22C55E', '#10B981', '#14B8A6',
  '#06B6D4', '#3B82F6', '#6366F1', '#8B5CF6',
  '#A855F7', '#D946EF', '#EC4899', '#6B7280',
];

export default function TagManagePage() {
  const { t } = useI18n();
  const { tags, loading, error, createTag, updateTag, deleteTag } = useTags();

  // Create form
  const [newName, setNewName] = useState('');
  const [newColor, setNewColor] = useState(COLOR_PALETTE[0]);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  // Edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editColor, setEditColor] = useState('');
  const [editError, setEditError] = useState('');

  // Delete confirmation
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState('');

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    setCreateError('');
    try {
      await createTag({ name: newName.trim(), color: newColor });
      setNewName('');
      setNewColor(COLOR_PALETTE[0]);
    } catch (err) {
      setCreateError((err as Error).message || 'Failed to create tag');
    } finally {
      setCreating(false);
    }
  }

  function startEdit(tag: TagDetail) {
    setEditingId(tag.id);
    setEditName(tag.name);
    setEditColor(tag.color);
    setEditError('');
  }

  function cancelEdit() {
    setEditingId(null);
    setEditName('');
    setEditColor('');
    setEditError('');
  }

  async function handleUpdate(tagId: string) {
    if (!editName.trim()) return;
    try {
      await updateTag(tagId, { name: editName.trim(), color: editColor });
      cancelEdit();
    } catch (err) {
      setEditError((err as Error).message || 'Failed to update tag');
    }
  }

  async function handleDelete(tagId: string) {
    try {
      await deleteTag(tagId);
      setDeletingId(null);
    } catch (err) {
      setDeleteError((err as Error).message || 'Failed to delete tag');
    }
  }

  if (loading) return <LoadingSkeleton variant="table-row" rows={8} />;

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t('tags.title')}</h1>

      {/* Create Tag Form */}
      <div className="glass-panel p-4">
        <h2 className="mb-3 text-lg font-semibold text-[var(--text-primary)]">{t('tags.create')}</h2>
        <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)]">{t('tags.name')}</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="mt-1 glass-select text-sm"
              placeholder="Tag name"
              maxLength={64}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)]">{t('tags.color')}</label>
            <div className="mt-1 flex flex-wrap gap-1">
              {COLOR_PALETTE.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setNewColor(c)}
                  className={`h-6 w-6 rounded border-2 ${newColor === c ? 'border-gray-800 scale-110' : 'border-transparent'}`}
                  style={{ backgroundColor: c }}
                  aria-label={`Color ${c}`}
                />
              ))}
            </div>
          </div>
          <button
            type="submit"
            disabled={creating || !newName.trim()}
            className="glass-btn glass-btn-primary glass-btn-sm"
          >
            {creating ? t('tags.creating') : t('tags.createBtn')}
          </button>
        </form>
        {createError && <p className="mt-2 text-sm text-red-600">{createError}</p>}
      </div>

      {/* Tags Table */}
      <div className="glass-panel overflow-x-auto">
        {tags.length === 0 ? (
          <div className="p-12 text-center text-sm text-[var(--text-tertiary)]">{t('tags.noTags')}</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-[rgba(0,0,0,0.06)] bg-white/20">
              <tr>
                <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('tags.tag')}</th>
                <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('tags.color')}</th>
                <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('tags.papers')}</th>
                <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('tags.repos')}</th>
                <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('tags.created')}</th>
                <th className="px-4 py-3 font-medium text-[var(--text-secondary)]">{t('tags.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[rgba(0,0,0,0.06)]">
              {tags.map((tag) => (
                <tr key={tag.id} className="hover:bg-white/20">
                  {editingId === tag.id ? (
                    <>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          className="glass-input h-[32px] w-full px-2 py-1 text-sm"
                          maxLength={64}
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {COLOR_PALETTE.map((c) => (
                            <button
                              key={c}
                              type="button"
                              onClick={() => setEditColor(c)}
                              className={`h-5 w-5 rounded border-2 ${editColor === c ? 'border-gray-800 scale-110' : 'border-transparent'}`}
                              style={{ backgroundColor: c }}
                              aria-label={`Color ${c}`}
                            />
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-[var(--text-secondary)]">{tag.paper_count}</td>
                      <td className="px-4 py-3 text-[var(--text-secondary)]">{tag.repo_count}</td>
                      <td className="px-4 py-3 text-[var(--text-secondary)]">{new Date(tag.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => handleUpdate(tag.id)}
                            className="text-sm text-blue-600 hover:underline"
                          >
                            Save
                          </button>
                          <button
                            type="button"
                            onClick={cancelEdit}
                            className="text-sm text-[var(--text-secondary)] hover:underline"
                          >
                            Cancel
                          </button>
                          {editError && <span className="text-xs text-red-600">{editError}</span>}
                        </div>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-3">
                        <span
                          className="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-sm font-medium"
                          style={tagBadgeStyle(tag.color)}
                        >
                          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: tag.color }} />
                          {tag.name}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center gap-1 text-sm">
                          <span className="h-3 w-3 rounded" style={{ backgroundColor: tag.color }} />
                          {tag.color}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium text-[var(--text-primary)]">{tag.paper_count}</td>
                      <td className="px-4 py-3 font-medium text-[var(--text-primary)]">{tag.repo_count}</td>
                      <td className="px-4 py-3 text-[var(--text-secondary)]">{new Date(tag.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => startEdit(tag)}
                            className="text-sm text-blue-600 hover:underline"
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeletingId(tag.id)}
                            className="text-sm text-red-600 hover:underline"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {deleteError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{deleteError}</div>
      )}

      {/* Delete Confirmation Dialog */}
      {deletingId && (
        <div className="glass-modal-overlay">
          <div className="glass-modal">
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{t('tags.deleteTitle')}</h3>
            <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
              {t('tags.deleteConfirm')}
            </p>
            <div className="mt-4 flex justify-end gap-3">
              <button type="button" onClick={() => setDeletingId(null)}
                className="glass-btn glass-btn-secondary glass-btn-sm">{t('tags.cancel')}</button>
              <button type="button" onClick={() => handleDelete(deletingId)}
                className="glass-btn glass-btn-danger glass-btn-sm">{t('tags.delete')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
