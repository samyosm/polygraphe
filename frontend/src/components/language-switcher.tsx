"use client";

import { ChevronDown, Language } from "@carbon/icons-react";
import { useLocale, useTranslations } from "next-intl";
import { useTransition } from "react";
import { setLocale } from "@/i18n/actions";
import { localeNames, locales } from "@/i18n/config";
import { cn } from "./ui/cn";

export function LanguageSwitcher() {
  const t = useTranslations("header");
  const locale = useLocale();
  const [pending, startTransition] = useTransition();

  return (
    <label
      className={cn(
        "relative flex h-10 items-center gap-2 px-2 text-ink-muted hover:bg-layer-hover hover:text-ink",
        "focus-within:outline-2 focus-within:outline-focus",
        pending && "opacity-60",
      )}
    >
      <Language size={20} aria-hidden />
      <span className="sr-only">{t("language")}</span>
      <select
        value={locale}
        disabled={pending}
        onChange={(e) => startTransition(() => setLocale(e.target.value))}
        className="cursor-pointer appearance-none bg-transparent pr-5 text-sm text-ink outline-none"
      >
        {locales.map((value) => (
          <option key={value} value={value} lang={value}>
            {localeNames[value]}
          </option>
        ))}
      </select>
      <ChevronDown
        size={16}
        aria-hidden
        className="pointer-events-none absolute right-2"
      />
    </label>
  );
}
