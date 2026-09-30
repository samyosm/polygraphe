import { useFormatter, useTranslations } from "next-intl";
import { Container } from "@/components/container";
import { TEAM } from "@/lib/project";

export function Hero() {
  const t = useTranslations("hero");
  const format = useFormatter();

  return (
    <section className="relative overflow-hidden border-b border-line bg-layer">
      <HeartbeatLine />
      <Container className="relative flex flex-col gap-6 py-16 md:py-24">
        <p className="text-sm text-interactive">{t("eyebrow")}</p>
        <h1 className="text-5xl font-light tracking-tight md:text-7xl">
          <span className="font-semibold">Poly</span>Graphe
        </h1>
        <p className="max-w-2xl text-lg font-light text-ink-muted md:text-xl">
          {t("lead")}
        </p>
        <p className="flex flex-col gap-1 pt-4">
          <span className="text-xs tracking-[0.32px] text-ink-muted">
            {t("madeBy")}
          </span>
          <span className="text-xl font-light">
            {format.list(TEAM, { type: "conjunction" })}
          </span>
        </p>
      </Container>
    </section>
  );
}

/** One heartbeat (P wave, QRS complex, T wave), then a flat line; 200 units wide. */
const BEAT =
  "h40 l8,-6 l8,6 h14 l5,10 l9,-64 l9,70 l5,-16 h18 l12,-10 l12,10 h60";
const BEATS = 6;

/** Decorative ECG trace on wide screens, revealed from left to right on load. */
function HeartbeatLine() {
  return (
    <svg
      viewBox={`0 0 ${BEATS * 200} 120`}
      preserveAspectRatio="none"
      aria-hidden="true"
      className="pointer-events-none absolute inset-y-0 right-0 hidden h-full w-2/5 animate-reveal xl:block"
    >
      <path
        d={`M0,80 ${BEAT.repeat(BEATS)}`}
        fill="none"
        strokeWidth={1.5}
        vectorEffect="non-scaling-stroke"
        className="stroke-interactive opacity-40"
      />
    </svg>
  );
}
