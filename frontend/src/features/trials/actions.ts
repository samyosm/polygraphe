"use server";

import { refresh } from "next/cache";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { operatorApi } from "@/lib/api/operator";
import type { Sex, TrialDetails } from "@/lib/api/types";

export type ActionResult = { error: string } | undefined;

/** Translated message for a failed call, by HTTP status. */
async function failure(response: Response): Promise<ActionResult> {
  const t = await getTranslations("errors");
  const keys: Record<number, "unauthorized" | "conflict" | "invalid"> = {
    401: "unauthorized",
    409: "conflict",
    422: "invalid",
  };
  const key = keys[response.status] ?? "unexpected";
  return { error: t(key) };
}

function text(form: FormData, name: string): string | undefined {
  const value = form.get(name);
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

/** Form fields -> API body. Empty fields are omitted, which clears them on update. */
function parseDetails(form: FormData): TrialDetails {
  const age = text(form, "age");
  return {
    title: text(form, "title") ?? "",
    description: text(form, "description"),
    subject: {
      name: text(form, "name"),
      age: age === undefined ? undefined : Number(age),
      sex: text(form, "sex") as Sex | undefined,
      culture: text(form, "culture"),
    },
  };
}

async function titleRequired(): Promise<ActionResult> {
  return { error: (await getTranslations("errors"))("titleRequired") };
}

export async function createTrial(
  _: ActionResult,
  form: FormData,
): Promise<ActionResult> {
  const body = parseDetails(form);
  if (!body.title) return titleRequired();

  const { data, response } = await (await operatorApi()).POST("/trials", {
    body,
  });
  if (!data) return failure(response);
  redirect(`/trials/${data.id}`);
}

export async function updateTrial(
  trialId: string,
  _: ActionResult,
  form: FormData,
): Promise<ActionResult> {
  const body = parseDetails(form);
  if (!body.title) return titleRequired();

  const { data, response } = await (await operatorApi()).PUT(
    "/trials/{trial_id}",
    {
      params: trialPath(trialId),
      body,
    },
  );
  if (!data) return failure(response);
  redirect(`/trials/${trialId}`);
}

const trialPath = (trialId: string) => ({ path: { trial_id: trialId } });

/** Refreshes the page on success, so it shows the trial's new status. */
async function settle({
  error,
  response,
}: {
  error?: unknown;
  response: Response;
}) {
  if (error) return failure(response);
  refresh();
}

export async function startRecording(trialId: string, deviceId: string) {
  return settle(
    await (await operatorApi()).POST("/trials/{trial_id}/start", {
      params: trialPath(trialId),
      body: { device_id: deviceId },
    }),
  );
}

/** Stops data intake; it can be resumed later. */
export async function stopRecording(trialId: string) {
  return settle(
    await (await operatorApi()).POST("/trials/{trial_id}/stop", {
      params: trialPath(trialId),
    }),
  );
}

/** Stops data intake for good. */
export async function completeTrial(trialId: string) {
  return settle(
    await (await operatorApi()).POST("/trials/{trial_id}/complete", {
      params: trialPath(trialId),
    }),
  );
}
