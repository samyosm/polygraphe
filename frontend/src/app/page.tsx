import { Add } from "@carbon/icons-react";
import { getTranslations } from "next-intl/server";
import { Container } from "@/components/container";
import { ButtonLink } from "@/components/ui/button";
import { Hero } from "@/features/home/hero";
import { LiveRecordings } from "@/features/live/live-recordings";
import { RefreshOnTrialChange } from "@/features/trials/refresh-on-change";
import { TrialSearch } from "@/features/trials/trial-search";
import { TrialTable } from "@/features/trials/trial-table";
import { isOperator } from "@/lib/api/operator";
import { listRecordingTrials, listTrials } from "@/lib/api/queries";

export default async function HomePage({ searchParams }: PageProps<"/">) {
  const { q } = await searchParams;
  const search = typeof q === "string" ? q.trim() : "";
  const [trials, recording, operator, t] = await Promise.all([
    listTrials(search),
    listRecordingTrials(),
    isOperator(),
    getTranslations("trials"),
  ]);
  const isEmpty = trials.length === 0 && !search;

  return (
    <>
      <RefreshOnTrialChange />
      <Hero />
      <Container className="flex flex-col gap-16 py-12">
        <LiveRecordings trials={recording} />

        <section className="flex flex-col gap-8">
          <div className="flex min-h-12 items-end justify-between gap-4">
            <h2 className="text-3xl font-light">{t("title")}</h2>
            {operator && (
              <ButtonLink href="/trials/new" icon={Add}>
                {t("new")}
              </ButtonLink>
            )}
          </div>

          {isEmpty ? (
            <div className="flex flex-col gap-2 border-t border-line py-12">
              <p className="text-xl font-light">{t("emptyTitle")}</p>
              <p className="text-ink-muted">{t("emptyText")}</p>
            </div>
          ) : (
            <>
              <TrialSearch initial={search} />
              {/* A floor on the height, so narrowing results does not pull the page up. */}
              <div className="min-h-[70vh]">
                {trials.length === 0 ? (
                  <p className="text-ink-muted">{t("noMatch", { search })}</p>
                ) : (
                  <TrialTable trials={trials} />
                )}
              </div>
            </>
          )}
        </section>
      </Container>
    </>
  );
}
