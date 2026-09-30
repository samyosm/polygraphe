import { useTranslations } from "next-intl";
import { useCallback } from "react";
import type { Stage } from "@/lib/api/types";

interface KindConfig {
  unit?: string;
  /** Fields to plot, in order; the first one is the headline value. Default: all of them. */
  fields?: string[];
}

/**
 * How known measurement kinds are displayed; their names are translated under `kinds` in
 * the messages. Kinds missing from here are still shown, with a name derived from their
 * identifier and every numeric field plotted. The order of this object is the order of
 * the charts.
 */
const KINDS: Record<string, KindConfig> = {
  heart_rate: { unit: "bpm" },
  spo2: { unit: "%" },
  breathing_rate: { unit: "/min" },
  sweat: {},
  gsr: { unit: "µS" },
  heart_rate_stats: { unit: "bpm", fields: ["mean", "min", "max"] },
  spo2_stats: { unit: "%", fields: ["mean", "min"] },
};

const ORDER = Object.keys(KINDS);

/** Most important first. */
export const STAGES: Stage[] = ["processed", "raw"];

export interface FieldDisplay {
  key: string;
  label: string;
}

export interface KindDisplay {
  label: string;
  unit?: string;
  fields: FieldDisplay[];
}

/** Stable across renders (per language): charts are rebuilt when their fields change. */
export function useKindDisplay() {
  const t = useTranslations();

  return useCallback(
    (kind: string, availableFields: readonly string[]): KindDisplay => {
      // Kinds and fields are open-ended, so their keys cannot be checked at compile time.
      const translate = (namespace: "kinds" | "fields", key: string) => {
        const id = `${namespace}.${key}` as Parameters<typeof t>[0];
        return t.has(id) ? t(id) : humanize(key);
      };
      const config = KINDS[kind];
      return {
        label: translate("kinds", kind),
        unit: config?.unit,
        fields: (config?.fields ?? availableFields).map((key) => ({
          key,
          label: translate("fields", key),
        })),
      };
    },
    [t],
  );
}

/** Known kinds first, in declaration order, then the others alphabetically. */
export function compareKinds(a: string, b: string): number {
  const rank = (kind: string) => {
    const index = ORDER.indexOf(kind);
    return index === -1 ? ORDER.length : index;
  };
  return rank(a) - rank(b) || a.localeCompare(b);
}

function humanize(name: string): string {
  const words = name.replace(/[_.-]+/g, " ").trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}
