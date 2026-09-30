import Link from "next/link";
import { useFormatter, useTranslations } from "next-intl";
import type { Trial } from "@/lib/api/types";
import { TrialStatusTag } from "./status";
import { useDescribeSubject } from "./subject";

export function TrialTable({ trials }: { trials: Trial[] }) {
  const t = useTranslations("trials.columns");
  const format = useFormatter();
  const describeSubject = useDescribeSubject();

  return (
    <table className="w-full text-left">
      <thead>
        <tr className="border-b border-line-strong text-ink-muted">
          <th className="py-3 pr-4 font-normal">{t("title")}</th>
          <th className="hidden py-3 pr-4 font-normal md:table-cell">
            {t("subject")}
          </th>
          <th className="py-3 pr-4 font-normal">{t("status")}</th>
          <th className="hidden py-3 font-normal sm:table-cell">
            {t("created")}
          </th>
        </tr>
      </thead>
      <tbody>
        {trials.map((trial) => (
          <tr
            key={trial.id}
            className="relative border-b border-line hover:bg-layer"
          >
            <td className="py-4 pr-4">
              {/* The link covers the whole row (see `after:`). */}
              <Link
                href={`/trials/${trial.id}`}
                className="outline-none after:absolute after:inset-0 focus-visible:underline"
              >
                {trial.title}
              </Link>
            </td>
            <td className="hidden py-4 pr-4 text-ink-muted md:table-cell">
              {describeSubject(trial.subject) ?? "—"}
            </td>
            <td className="py-4 pr-4">
              <TrialStatusTag status={trial.status} />
            </td>
            <td className="hidden py-4 text-ink-muted sm:table-cell">
              {format.dateTime(new Date(trial.created_at), {
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
