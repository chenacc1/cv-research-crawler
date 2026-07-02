import { NavLink } from 'react-router-dom';
import { useI18n } from '../../i18n/I18nProvider';

export default function Sidebar() {
  const { t, lang, toggleLang } = useI18n();

  const navItems = [
    { to: '/', label: t('nav.dashboard') },
    { to: '/papers', label: t('nav.papers') },
    { to: '/repos', label: t('nav.repos') },
    { to: '/tags', label: t('nav.tags') },
    { to: '/reports', label: t('nav.reports') },
    { to: '/crawls', label: t('nav.crawls') },
    { to: '/keywords', label: t('nav.keywords') },
  ];

  return (
    <aside
      className="flex h-screen w-56 flex-shrink-0 flex-col border-r"
      style={{
        background: 'var(--glass-panel)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderColor: 'rgba(255,255,255,0.2)',
        boxShadow: 'var(--nue-highlight), var(--nue-shadow)',
      }}
    >
      <div className="flex h-14 items-center gap-2 border-b px-4" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
        <span className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
          {t('app.title')}
        </span>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                isActive
                  ? 'bg-opacity-15'
                  : 'text-[var(--text-secondary)]'
              }`
            }
            style={({ isActive }) =>
              isActive
                ? {
                    background: 'rgba(116,95,242,0.12)',
                    color: 'var(--purple)',
                    border: '1px solid rgba(116,95,242,0.2)',
                    boxShadow: 'var(--nue-highlight), inset -1px -1px 2px rgba(0,0,0,0.04), var(--rim-b1), var(--rim-b2)',
                  }
                : {}
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t px-4 py-3 space-y-2" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
        <button
          type="button"
          onClick={toggleLang}
          className="glass-btn glass-btn-secondary w-full"
          style={{ height: 34, fontSize: 13 }}
        >
          {t('shared.langBtn')}
        </button>
        <p className="text-xs text-[var(--text-tertiary)]">CV Research Crawler v1.0</p>
      </div>
    </aside>
  );
}
