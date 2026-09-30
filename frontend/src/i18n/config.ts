export const locales = ["en", "fr"] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "en";

/** Cookie holding the language picked in the header. */
export const LOCALE_COOKIE = "NEXT_LOCALE";

/** Each language is named in itself, as is customary in language pickers. */
export const localeNames: Record<Locale, string> = {
  en: "English",
  fr: "Français",
};

export function isLocale(value: unknown): value is Locale {
  return locales.includes(value as Locale);
}
