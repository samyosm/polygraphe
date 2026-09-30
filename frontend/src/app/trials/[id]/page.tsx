import { ArrowLeft, Edit } from "@carbon/icons-react";
import type { Metadata } from "next";
import Link from "next/link";
import { useFormatter, useTranslations } from "next-intl";
import { getTranslations } from "next-intl/server";
import { Container } from "@/components/container";
import { ButtonLink } from "@/components/ui/button";
import { MeasurementBoard } from "@/features/measurements/measurement-board";
import { RefreshOnTrialChange } from "@/features/trials/refresh-on-change";
import { TrialStatusTag } from "@/features/trials/status";
import { useDescribeSubject } from "@/features/trials/subject";
import { TrialControls } from "@/features/trials/trial-controls";
import { isOperator } from "@/lib/api/operator";
import { getTrial, getTrialMeasurements, listDevices } from "@/lib/api/queries";
import type { Trial } from "@/lib/api/types";

export async function generateMetadata({
  params,
}: PageProps<"/trials/[id]">): Promise<Metadata> {
  const trial = await getTrial((await params).id);
  return { title: trial.title };
}

export default async function TrialPage({ params }: PageProps<"/trials/[id]">) {
  const { id } = await params;
  const [trial, measurements, devices, operator, t] = await Promise.all([
    getTrial(id),
    getTrialMeasurements(id),
    listDevices(),
    isOperator(),
    getTranslations("trials"),
  ]);
  const openSegment = trial.segments.find((s) => s.stopped_at === null);

  return (
    <Container className="flex flex-col gap-10 py-10">
      <RefreshOnTrialChange trialId={trial.id} />
      <div className="flex flex-col gap-6">
        <Link
          href="/"
          className="flex w-fit items-center gap-2 text-interactive hover:underline"
        >
          <ArrowLeft size={16} aria-hidden /> {t("back")}
        </Link>

        <div className="flex flex-wrap items-start justify-between gap-4">
          <TrialSummary trial={trial} />
          {operator && (
            <ButtonLink
              href={`/trials/${trial.id}/edit`}
              variant="ghost"
              icon={Edit}
            >
              {t("edit")}
            </ButtonLink>
          )}
        </div>

        {operator && <TrialControls trial={trial} devices={devices} />}
      </div>

      <MeasurementBoard
        key={trial.id}
        trialId={trial.id}
        initial={measurements}
        live={trial.status === "recording"}
        recordingSince={openSegment?.started_at}
      />
    </Container>
  );
}

function TrialSummary({ trial }: { trial: Trial }) {
  const t = useTranslations("trials");
  const format = useFormatter();
  const describeSubject = useDescribeSubject();
  const created = t("created", {
    date: format.dateTime(new Date(trial.created_at), {
      dateStyle: "medium",
      timeStyle: "short",
    }),
  });

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-4">
        <h1 className="text-4xl font-light">{trial.title}</h1>
        <TrialStatusTag status={trial.status} />
      </div>
      <p className="text-ink-muted">
        {[describeSubject(trial.subject), created].filter(Boolean).join(" — ")}
      </p>
      {trial.description && (
        <p className="max-w-3xl whitespace-pre-line">{trial.description}</p>
      )}
    </div>
  );
}
