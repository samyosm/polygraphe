"use client";

import type { Measurement } from "@/lib/api/types";
import {
  type SocketStatus,
  useReconnectingSocket,
} from "@/lib/use-reconnecting-socket";
import type { MeasurementStore } from "./store";

/**
 * Streams a trial's live measurements into `store` while `enabled`.
 *
 * Each (re)connection asks the server for everything since the newest point already
 * held (or since `since` when the store is empty), so reconnecting never leaves holes.
 */
export function useLiveFeed(
  store: MeasurementStore,
  trialId: string,
  since: string | undefined,
  enabled: boolean,
): SocketStatus {
  return useReconnectingSocket({
    path: enabled ? `/trials/${trialId}/live` : null,
    params: () => ({ since: store.latestTimestamp ?? since }),
    onMessage: (data) => store.add(data as Measurement),
  });
}
