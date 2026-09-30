import { Locked } from "@carbon/icons-react";
import { useTranslations } from "next-intl";

/** Shown instead of a control page to visitors who are not in operator mode. */
export function OperatorRequired() {
  const t = useTranslations("operator");
  return (
    <div className="flex flex-col items-start gap-3 border-t border-line py-12">
      <Locked size={24} aria-hidden className="text-ink-muted" />
      <p className="text-xl font-light">{t("required")}</p>
      <p className="text-ink-muted">{t("requiredHint")}</p>
    </div>
  );
}
