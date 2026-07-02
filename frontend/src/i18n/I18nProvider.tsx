import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { Lang } from '../i18n/translations';
import { tr } from '../i18n/translations';

interface I18nContextType {
  lang: Lang;
  toggleLang: () => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

const STORAGE_KEY = 'cv-crawler-lang';

function getStoredLang(): Lang {
  try {
    return (localStorage.getItem(STORAGE_KEY) as Lang) || 'zh';
  } catch {
    return 'zh';
  }
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(getStoredLang);

  const toggleLang = useCallback(() => {
    setLang((prev) => {
      const next = prev === 'zh' ? 'en' : 'zh';
      try { localStorage.setItem(STORAGE_KEY, next); } catch { /* noop */ }
      return next;
    });
  }, []);

  const tFn = useCallback(
    (key: string, vars?: Record<string, string | number>) => tr(lang, key, vars),
    [lang],
  );

  return (
    <I18nContext.Provider value={{ lang, toggleLang, t: tFn }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n(): I18nContextType {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
}
