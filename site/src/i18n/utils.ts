import en from './en.json';
import tr from './tr.json';
import nl from './nl.json';

export const LOCALES = ['en', 'tr', 'nl'] as const;
export type Locale = (typeof LOCALES)[number];

const dicts: Record<Locale, Record<string, string>> = { en, tr, nl };

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}

export function useTranslations(lang: string) {
  const dict: Record<string, string> = isLocale(lang) ? dicts[lang] : dicts.en;
  return (key: string): string => dict[key] ?? dicts.en[key] ?? key;
}
