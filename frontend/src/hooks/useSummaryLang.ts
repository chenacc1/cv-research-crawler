import { useI18n } from '../i18n/I18nProvider';

export function useSummaryLang() {
  const { lang, toggleLang } = useI18n();
  return { lang: lang === 'zh' ? 'cn' as const : 'en' as const, toggleLang };
}
