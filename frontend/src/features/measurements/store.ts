import type { Measurement, Stage } from "@/lib/api/types";

/** Longer silences than this (s) are drawn as gaps, e.g. between two recording periods. */
const GAP_SECONDS = 10;

type Listener = () => void;

class Emitter {
  private listeners = new Set<Listener>();

  /** Arrow function so it can be passed around unbound (e.g. to useSyncExternalStore). */
  subscribe = (listener: Listener) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };

  protected emit() {
    for (const listener of this.listeners) listener();
  }
}

/**
 * One time series (a stage + kind pair), stored column-wise as uPlot wants it:
 * a shared time column (Unix seconds) and one value column per numeric field.
 */
export class Series extends Emitter {
  readonly times: number[] = [];
  private columns = new Map<string, (number | null)[]>();
  /** Replaced (never mutated) when a field appears, so it can be used as a dependency. */
  fields: readonly string[] = [];

  constructor(
    readonly stage: Stage,
    readonly kind: string,
  ) {
    super();
  }

  /** Appends a point. Points not newer than the last one are ignored (duplicates). */
  append(time: number, values: Record<string, number>): boolean {
    const last = this.times.at(-1);
    if (last !== undefined && time <= last) return false;
    if (last !== undefined && time - last > GAP_SECONDS)
      this.pushRow((last + time) / 2, {});
    this.pushRow(time, values);
    this.emit();
    return true;
  }

  column(field: string): readonly (number | null)[] {
    return this.columns.get(field) ?? [];
  }

  latest(field: string): number | null {
    return this.columns.get(field)?.at(-1) ?? null;
  }

  private pushRow(time: number, values: Record<string, number>) {
    for (const field of Object.keys(values)) {
      if (!this.columns.has(field)) {
        this.columns.set(field, new Array(this.times.length).fill(null));
        this.fields = [...this.fields, field];
      }
    }
    this.times.push(time);
    for (const [field, column] of this.columns)
      column.push(values[field] ?? null);
  }
}

const seriesKey = (stage: Stage, kind: string) => `${stage}/${kind}`;

/** Every series of a trial. Notifies subscribers only when a new series appears. */
export class MeasurementStore extends Emitter {
  private series = new Map<string, Series>();
  private list: readonly Series[] = [];
  /** Original ISO timestamp of the newest point, to resume a live feed without losing precision. */
  latestTimestamp: string | undefined;
  private latestTime = Number.NEGATIVE_INFINITY;

  constructor(initial: Measurement[] = []) {
    super();
    for (const measurement of initial) this.add(measurement);
  }

  getSeries = () => this.list;

  add(measurement: Measurement) {
    const time = Date.parse(measurement.timestamp) / 1000;
    const values = numericFields(measurement.fields);
    if (Number.isNaN(time) || Object.keys(values).length === 0) return;

    const appended = this.getOrCreate(
      measurement.stage,
      measurement.kind,
    ).append(time, values);
    if (appended && time > this.latestTime) {
      this.latestTime = time;
      this.latestTimestamp = measurement.timestamp;
    }
  }

  private getOrCreate(stage: Stage, kind: string): Series {
    const key = seriesKey(stage, kind);
    let series = this.series.get(key);
    if (!series) {
      series = new Series(stage, kind);
      this.series.set(key, series);
      this.list = [...this.list, series];
      this.emit();
    }
    return series;
  }
}

function numericFields(fields: Measurement["fields"]): Record<string, number> {
  const values: Record<string, number> = {};
  for (const [field, value] of Object.entries(fields)) {
    if (typeof value === "number" && Number.isFinite(value))
      values[field] = value;
  }
  return values;
}
