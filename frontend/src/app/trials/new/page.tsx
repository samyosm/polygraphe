import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { Container } from "@/components/container";
import { OperatorRequired } from "@/features/operator/operator-required";
import { TrialForm } from "@/features/trials/trial-form";
import { isOperator } from "@/lib/api/operator";

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getTranslations("form"))("newTitle") };
}

export default async function NewTrialPage() {
  const [t, operator] = await Promise.all([
    getTranslations("form"),
    isOperator(),
  ]);
  return (
    <Container className="flex flex-col gap-10 py-10">
      <h1 className="text-4xl font-light">{t("newTitle")}</h1>
      {operator ? <TrialForm /> : <OperatorRequired />}
    </Container>
  );
}
