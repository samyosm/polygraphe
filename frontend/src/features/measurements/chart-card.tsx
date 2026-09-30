"use client";

import { useFormatter } from "next-intl";
import { useMemo, useSyncExternalStore } from "react";
import { useKindDisplay } from "./kinds";
import type { Series } from "./store";
import { TimeSeriesChart } from "./time-series-chart";

export function ChartCard({ series, live }: { series: Series; live: boolean }) {
  const format = useFormatter();
  const describeKind = useKindDisplay();
  const availableFields = useSyncExternalStore(
    series.subscribe,
    () => series.fields,
    () => series.fields,
  );
  const display = useMemo(
    () => describeKind(series.kind, availableFields),
    [describeKind, series.kind, availableFields],
  );
  const headline = display.fields[0]?.key;
  const latest = useSyncExternalStore(
    series.subscribe,
    () => (headline ? series.latest(headline) : null),
    () => null,
  );

  return (
    <section className="flex flex-col gap-4 bg-layer p-4">
      <header className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h3>{display.label}</h3>
          {display.fields.length > 1 && (
            <ul className="flex gap-3 text-xs text-ink-muted">
              {display.fields.map((field, i) => (
                <li key={field.key} className="flex items-center gap-1.5">
                  <span
                    className="size-2"
                    style={{
                      backgroundColor: `var(--color-chart-${(i % 6) + 1})`,
                    }}
                  />
                  {field.label}
                </li>
              ))}
            </ul>
          )}
        </div>
        <p className="text-2xl font-light tabular-nums">
          {latest == null
            ? "—"
            : format.number(latest, { maximumFractionDigits: 1 })}
          {display.unit && (
            <span className="ml-1 text-sm text-ink-muted">{display.unit}</span>
          )}
        </p>
      </header>
      <TimeSeriesChart series={series} fields={display.fields} live={live} />
    </section>
  );
}
