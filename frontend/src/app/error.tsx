"use client";

import { Renew } from "@carbon/icons-react";
import { useTranslations } from "next-intl";
import { Container } from "@/components/container";
import { Button } from "@/components/ui/button";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  const t = useTranslations("errors");
  return (
    <Container className="flex flex-col items-start gap-8 py-16">
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-light">{t("genericTitle")}</h1>
        <p className="text-ink-muted">
          {t("serverDown")} {error.message && `(${error.message})`}
        </p>
      </div>
      <Button variant="tertiary" icon={Renew} onClick={reset}>
        {t("retry")}
      </Button>
    </Container>
  );
}
