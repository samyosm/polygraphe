"use client";

import { Search } from "@carbon/icons-react";
import Form from "next/form";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useRef, useTransition } from "react";
import { cn } from "@/components/ui/cn";
import { TextInput } from "@/components/ui/field";

const DEBOUNCE_MS = 250;

/**
 * Searches as you type. Results replace the URL's `?q=` without scrolling or adding
 * history entries, so the page stays where it is.
 */
export function TrialSearch({ initial }: { initial: string }) {
  const t = useTranslations("trials");
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);

  const search = (value: string) => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      const q = value.trim();
      startTransition(() =>
        router.replace(q ? `/?q=${encodeURIComponent(q)}` : "/", {
          scroll: false,
        }),
      );
    }, DEBOUNCE_MS);
  };

  return (
    // Still works without JavaScript, by submitting with Enter.
    <Form action="/" replace scroll={false} role="search" className="relative">
      <Search
        size={16}
        aria-hidden
        className={cn(
          "pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-ink-muted",
          pending && "animate-pulse",
        )}
      />
      <TextInput
        name="q"
        type="search"
        defaultValue={initial}
        onChange={(e) => search(e.target.value)}
        placeholder={t("searchPlaceholder")}
        aria-label={t("searchLabel")}
        className="h-12 pl-12"
      />
    </Form>
  );
}
