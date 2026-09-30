import { cookies, headers } from "next/headers";
import { getRequestConfig } from "next-intl/server";
import { defaultLocale, isLocale, LOCALE_COOKIE, type Locale } from "./config";

/**
 * The language is not part of the URL: it comes from the cookie set by the language
 * picker or, on a first visit, from the browser's preferences.
 */
export default getRequestConfig(async () => {
  const locale = await resolveLocale();
  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default,
    // Dates are shown in the server's time zone, the same on the server and in the browser.
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  };
});

async function resolveLocale(): Promise<Locale> {
  const fromCookie = (await cookies()).get(LOCALE_COOKIE)?.value;
  if (isLocale(fromCookie)) return fromCookie;

  // "fr-CA,fr;q=0.9,en;q=0.8" -> first supported language, in the browser's order.
  const accepted = (await headers()).get("accept-language") ?? "";
  for (const entry of accepted.split(",")) {
    const language = entry.split(";")[0].trim().slice(0, 2).toLowerCase();
    if (isLocale(language)) return language;
  }
  return defaultLocale;
}
