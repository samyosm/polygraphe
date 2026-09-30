"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import type { Trial } from "@/lib/api/types";
import { useReconnectingSocket } from "@/lib/use-reconnecting-socket";

/** Several changes often come together (e.g. stop then save): refresh once. */
const DEBOUNCE_MS = 150;

/**
 * Re-renders the page when trials change anywhere (another operator, another tab), so
 * watchers never need to reload. Limited to one trial when `trialId` is given.
 */
export function RefreshOnTrialChange({ trialId }: { trialId?: string }) {
  const router = useRouter();
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const refreshSoon = () => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => router.refresh(), DEBOUNCE_MS);
  };
  useEffect(() => () => clearTimeout(timer.current), []);

  useReconnectingSocket({
    path: "/trials/events",
    onMessage: (data) => {
      if (!trialId || (data as Trial).id === trialId) refreshSoon();
    },
    // Changes may have been missed while disconnected.
    onOpen: (reconnected) => reconnected && refreshSoon(),
  });

  return null;
}
