"use client";

import { ChevronDown } from "@carbon/icons-react";
import { useTranslations } from "next-intl";
import { type ReactNode, useId, useState, useSyncExternalStore } from "react";
import { cn } from "@/components/ui/cn";
import type { Measurement, Stage } from "@/lib/api/types";
import type { SocketStatus } from "@/lib/use-reconnecting-socket";
import { ChartCard } from "./chart-card";
import { compareKinds, STAGES } from "./kinds";
import { MeasurementStore, type Series } from "./store";
import { useLiveFeed } from "./use-live-feed";

/** Stages hidden until asked for: raw data matters less than what is derived from it. */
const COLLAPSED_BY_DEFAULT: ReadonlySet<Stage> = new Set(["raw"]);

interface Props {
  trialId: string;
  /** Measurements recorded so far, fetched by the server. */
  initial: Measurement[];
  live: boolean;
  /** Start of the current recording period, where the live feed starts on an empty trial. */
  recordingSince?: string;
}

/**
 * Processed and raw measurements of a trial, updated in real time while recording.
 * `initial` is only read on mount: from then on the store is the source of truth.
 */
export function MeasurementBoard({
  trialId,
  initial,
  live,
  recordingSince,
}: Props) {
  const t = useTranslations("measurements");
  const [store] = useState(() => new MeasurementStore(initial));
  const status = useLiveFeed(store, trialId, recordingSince, live);
  const allSeries = useSyncExternalStore(
    store.subscribe,
    store.getSeries,
    store.getSeries,
  );

  return (
    <div className="flex flex-col gap-12">
      {STAGES.map((stage, index) => (
        <StageSection
          key={stage}
          title={t(`${stage}.title`)}
          caption={t(`${stage}.caption`)}
          collapsible={COLLAPSED_BY_DEFAULT.has(stage)}
          aside={index === 0 && <FeedIndicator status={status} />}
        >
          <SeriesGrid
            series={allSeries
              .filter((s) => s.stage === stage)
              .toSorted((a, b) => compareKinds(a.kind, b.kind))}
            live={live}
          />
        </StageSection>
      ))}
    </div>
  );
}

function StageSection({
  title,
  caption,
  collapsible,
  aside,
  children,
}: {
  title: string;
  caption: string;
  collapsible: boolean;
  aside?: ReactNode;
  children: ReactNode;
}) {
  const t = useTranslations("measurements");
  const [open, setOpen] = useState(!collapsible);
  const contentId = useId();

  const heading = (
    <>
      {title} <span className="ml-2 text-sm text-ink-muted">{caption}</span>
    </>
  );

  return (
    <section className="flex flex-col gap-4">
      <h2 className="border-b border-line text-xl font-light">
        {collapsible ? (
          <button
            type="button"
            aria-expanded={open}
            aria-controls={contentId}
            onClick={() => setOpen(!open)}
            className="flex w-full items-center justify-between gap-4 pb-2 text-left outline-none hover:text-interactive focus-visible:outline-2 focus-visible:outline-focus"
          >
            <span>{heading}</span>
            <span className="flex items-center gap-2 text-sm text-interactive">
              {open ? t("hide") : t("show")}
              <ChevronDown
                size={16}
                aria-hidden
                className={cn("transition-transform", open && "rotate-180")}
              />
            </span>
          </button>
        ) : (
          <span className="flex items-baseline justify-between gap-4 pb-2">
            <span>{heading}</span>
            {aside}
          </span>
        )}
      </h2>
      {/* Collapsed charts are unmounted: no drawing cost while hidden. */}
      <div id={contentId} hidden={!open}>
        {open && children}
      </div>
    </section>
  );
}

function SeriesGrid({ series, live }: { series: Series[]; live: boolean }) {
  const t = useTranslations("measurements");
  if (series.length === 0) {
    return (
      <p className="py-8 text-ink-muted">{live ? t("waiting") : t("noData")}</p>
    );
  }
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {series.map((s) => (
        <ChartCard key={s.kind} series={s} live={live} />
      ))}
    </div>
  );
}

function FeedIndicator({ status }: { status: SocketStatus }) {
  const t = useTranslations("measurements");
  if (status === "idle") return null;
  return (
    <span className="text-xs text-ink-muted">
      {status === "open" ? t("live") : t("connecting")}
    </span>
  );
}
