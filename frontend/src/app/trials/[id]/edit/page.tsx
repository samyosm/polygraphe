import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { Container } from "@/components/container";
import { OperatorRequired } from "@/features/operator/operator-required";
import { TrialForm } from "@/features/trials/trial-form";
import { isOperator } from "@/lib/api/operator";
import { getTrial } from "@/lib/api/queries";

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getTranslations("form"))("editTitle") };
}

export default async function EditTrialPage({
  params,
}: PageProps<"/trials/[id]/edit">) {
  const [trial, t, operator] = await Promise.all([
    getTrial((await params).id),
    getTranslations("form"),
    isOperator(),
  ]);
  return (
    <Container className="flex flex-col gap-10 py-10">
      <h1 className="text-4xl font-light">{t("editTitle")}</h1>
      {operator ? <TrialForm trial={trial} /> : <OperatorRequired />}
    </Container>
  );
}
