import Link from "next/link";
import { useTranslations } from "next-intl";
import { MeasurementBoard } from "@/features/measurements/measurement-board";
import { TrialStatusTag } from "@/features/trials/status";
import { useDescribeSubject } from "@/features/trials/subject";
import type { Trial } from "@/lib/api/types";

/** Every recording in progress, with its data live: what watchers come for. */
export function LiveRecordings({ trials }: { trials: Trial[] }) {
  const t = useTranslations("live");
  if (trials.length === 0) return null;

  return (
    <section className="flex flex-col gap-10">
      <h2 className="text-3xl font-light">{t("title")}</h2>
      {trials.map((trial) => (
        <LiveRecording key={trial.id} trial={trial} />
      ))}
    </section>
  );
}

function LiveRecording({ trial }: { trial: Trial }) {
  const t = useTranslations("live");
  const describeSubject = useDescribeSubject();
  const segment = trial.segments.at(-1);
  const details = [
    describeSubject(trial.subject),
    t("device", { device: trial.recording_device ?? "—" }),
  ];

  return (
    <article className="flex flex-col gap-6 border-l-2 border-tag-red-ink pl-4 md:pl-6">
      <header className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={`/trials/${trial.id}`}
            className="text-2xl font-light hover:underline"
          >
            {trial.title}
          </Link>
          <TrialStatusTag status={trial.status} />
        </div>
        <p className="text-ink-muted">{details.filter(Boolean).join(" — ")}</p>
      </header>
      {/* Starts empty and backfills the current recording period over the websocket. */}
      <MeasurementBoard
        trialId={trial.id}
        initial={[]}
        live
        recordingSince={segment?.started_at}
      />
    </article>
  );
}
