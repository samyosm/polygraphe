"use client";

import { ArrowRight, Save } from "@carbon/icons-react";
import { useTranslations } from "next-intl";
import { useActionState } from "react";
import { Button, ButtonLink } from "@/components/ui/button";
import { Field, Select, TextArea, TextInput } from "@/components/ui/field";
import type { Trial } from "@/lib/api/types";
import { createTrial, updateTrial } from "./actions";
import { SEXES } from "./subject";

/** Creates a trial or, given one, edits its details. */
export function TrialForm({ trial }: { trial?: Trial }) {
  const t = useTranslations();
  const [state, action, pending] = useActionState(
    trial ? updateTrial.bind(null, trial.id) : createTrial,
    undefined,
  );
  const subject = trial?.subject;
  const optional = t("form.optional");

  return (
    <form action={action} className="flex max-w-2xl flex-col gap-8">
      <div className="flex flex-col gap-6">
        <Field label={t("form.title")}>
          <TextInput
            name="title"
            required
            maxLength={200}
            defaultValue={trial?.title}
            autoFocus
          />
        </Field>
        <Field label={t("form.description")} hint={optional}>
          <TextArea
            name="description"
            maxLength={5000}
            defaultValue={trial?.description ?? ""}
          />
        </Field>
      </div>

      <fieldset className="flex flex-col gap-6">
        <legend className="mb-6 text-base">
          {t("form.subject")}{" "}
          <span className="text-sm text-ink-muted">{optional}</span>
        </legend>
        <div className="grid gap-6 sm:grid-cols-2">
          <Field label={t("form.name")}>
            <TextInput
              name="name"
              maxLength={200}
              autoComplete="off"
              defaultValue={subject?.name ?? ""}
            />
          </Field>
          <Field label={t("form.age")}>
            <TextInput
              name="age"
              type="number"
              min={0}
              max={150}
              inputMode="numeric"
              defaultValue={subject?.age ?? ""}
            />
          </Field>
          <Field label={t("form.sex")}>
            <Select name="sex" defaultValue={subject?.sex ?? ""}>
              <option value="">—</option>
              {SEXES.map((sex) => (
                <option key={sex} value={sex}>
                  {t(`sex.${sex}`)}
                </option>
              ))}
            </Select>
          </Field>
          <Field label={t("form.culture")}>
            <TextInput
              name="culture"
              maxLength={200}
              defaultValue={subject?.culture ?? ""}
            />
          </Field>
        </div>
      </fieldset>

      {state?.error && (
        <p role="alert" className="text-support-error">
          {state.error}
        </p>
      )}

      <div className="grid grid-cols-2">
        <ButtonLink
          href={trial ? `/trials/${trial.id}` : "/"}
          variant="secondary"
        >
          {t("form.cancel")}
        </ButtonLink>
        {trial ? (
          <Button type="submit" icon={Save} disabled={pending}>
            {pending ? t("form.saving") : t("form.save")}
          </Button>
        ) : (
          <Button type="submit" icon={ArrowRight} disabled={pending}>
            {pending ? t("form.creating") : t("form.create")}
          </Button>
        )}
      </div>
    </form>
  );
}
