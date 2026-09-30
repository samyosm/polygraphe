import { useTranslations } from "next-intl";
import { Container } from "@/components/container";
import { ButtonLink } from "@/components/ui/button";

export default function NotFound() {
  const t = useTranslations("errors");
  return (
    <Container className="flex flex-col items-start gap-8 py-16">
      <h1 className="text-4xl font-light">{t("notFound")}</h1>
      <ButtonLink href="/" variant="tertiary">
        {t("backToTrials")}
      </ButtonLink>
    </Container>
  );
}
