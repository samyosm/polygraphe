import { useTranslations } from "next-intl";
import type { Subject } from "@/lib/api/types";

export const SEXES = ["female", "male", "other"] as const;

/** "Ada · 36 years · Female · British", or null when nothing is known. */
export function useDescribeSubject() {
  const t = useTranslations();
  return (subject: Subject): string | null => {
    const parts = [
      subject.name,
      subject.age != null && t("subject.age", { age: subject.age }),
      subject.sex && t(`sex.${subject.sex}`),
      subject.culture,
    ].filter(Boolean);
    return parts.length ? parts.join(" · ") : null;
  };
}
