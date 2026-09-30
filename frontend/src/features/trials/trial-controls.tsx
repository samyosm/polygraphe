"use client";

import { Pause, Play, Save } from "@carbon/icons-react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/field";
import type { Device, Trial } from "@/lib/api/types";
import {
  type ActionResult,
  completeTrial,
  startRecording,
  stopRecording,
} from "./actions";

const DEVICE_POLL_MS = 3000;

export function TrialControls({
  trial,
  devices,
}: {
  trial: Trial;
  devices: Device[];
}) {
  const t = useTranslations("controls");
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string>();
  const lastDevice = trial.segments.at(-1)?.device_id;
  const [deviceId, setDeviceId] = useState(
    devices.find((d) => d.id === lastDevice)?.id ?? devices[0]?.id,
  );

  const canStart = trial.status === "created" || trial.status === "paused";

  // While waiting for a device to connect, look again every few seconds.
  useEffect(() => {
    if (!canStart || devices.length > 0) return;
    const timer = setInterval(() => router.refresh(), DEVICE_POLL_MS);
    return () => clearInterval(timer);
  }, [canStart, devices.length, router]);

  const run = (action: () => Promise<ActionResult>) =>
    startTransition(async () => setError((await action())?.error));

  if (trial.status === "completed") return null;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-end gap-px">
        {canStart && (
          <>
            <DevicePicker
              devices={devices}
              value={deviceId}
              onChange={setDeviceId}
            />
            <Button
              icon={Play}
              disabled={pending || !deviceId}
              onClick={() =>
                deviceId && run(() => startRecording(trial.id, deviceId))
              }
            >
              {trial.status === "created" ? t("start") : t("resume")}
            </Button>
          </>
        )}
        {trial.status === "recording" && (
          <Button
            variant="secondary"
            icon={Pause}
            disabled={pending}
            onClick={() => run(() => stopRecording(trial.id))}
          >
            {t("stop")}
          </Button>
        )}
        {(trial.status === "recording" || trial.status === "paused") && (
          <Button
            icon={Save}
            disabled={pending}
            onClick={() => run(() => completeTrial(trial.id))}
          >
            {trial.status === "recording" ? t("stopAndSave") : t("save")}
          </Button>
        )}
      </div>
      {error && (
        <p role="alert" className="text-support-error">
          {error}
        </p>
      )}
    </div>
  );
}

function DevicePicker({
  devices,
  value,
  onChange,
}: {
  devices: Device[];
  value: string | undefined;
  onChange: (id: string) => void;
}) {
  const t = useTranslations("controls");
  if (devices.length === 0) {
    return (
      <p className="flex h-12 items-center pr-4 text-ink-muted">
        {t("waitingForDevice")}
      </p>
    );
  }
  return (
    <Select
      aria-label={t("device")}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-12 w-48"
    >
      {devices.map((device) => (
        <option key={device.id} value={device.id}>
          {device.id} ({device.source})
        </option>
      ))}
    </Select>
  );
}
