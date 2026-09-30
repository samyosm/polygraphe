import "server-only";

import { api, unwrap } from "./client";

export async function listTrials(search?: string) {
  return unwrap(
    await api.GET("/trials", { params: { query: { q: search || undefined } } }),
  );
}

/** Trials being recorded right now: at most one per device. */
export async function listRecordingTrials() {
  return unwrap(
    await api.GET("/trials", { params: { query: { status: "recording" } } }),
  );
}

export async function getTrial(trialId: string) {
  return unwrap(
    await api.GET("/trials/{trial_id}", {
      params: { path: { trial_id: trialId } },
    }),
  );
}

export async function getTrialMeasurements(trialId: string) {
  return unwrap(
    await api.GET("/trials/{trial_id}/measurements", {
      params: { path: { trial_id: trialId } },
    }),
  );
}

export async function listDevices() {
  return unwrap(await api.GET("/devices"));
}
