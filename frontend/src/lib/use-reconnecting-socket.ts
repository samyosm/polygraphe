"use client";

import { useEffect, useRef, useState } from "react";
import { WS_URL } from "@/lib/config";

export type SocketStatus = "idle" | "connecting" | "open";

const MAX_RETRY_MS = 10_000;

interface Options {
  /** Server path, e.g. "/trials/events"; null to stay disconnected. */
  path: string | null;
  /** Query parameters, evaluated at each (re)connection. */
  params?: () => Record<string, string | undefined>;
  onMessage: (data: unknown) => void;
  /** Called on every successful connection; `reconnected` is false the first time. */
  onOpen?: (reconnected: boolean) => void;
}

/** A websocket to the processing server that reconnects with exponential backoff. */
export function useReconnectingSocket({
  path,
  params,
  onMessage,
  onOpen,
}: Options): SocketStatus {
  const [status, setStatus] = useState<SocketStatus>("idle");
  // Latest callbacks, without reconnecting when their identity changes.
  const callbacks = useRef({ params, onMessage, onOpen });
  useEffect(() => {
    callbacks.current = { params, onMessage, onOpen };
  });

  useEffect(() => {
    if (path === null) {
      setStatus("idle");
      return;
    }
    let socket: WebSocket | undefined;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let opened = false;
    let disposed = false;

    const connect = () => {
      // Concatenation, not new URL(path, base): the base may have a path ("/api").
      const url = new URL(WS_URL + path);
      for (const [key, value] of Object.entries(
        callbacks.current.params?.() ?? {},
      )) {
        if (value !== undefined) url.searchParams.set(key, value);
      }
      setStatus("connecting");
      socket = new WebSocket(url);
      socket.onopen = () => {
        attempt = 0;
        setStatus("open");
        callbacks.current.onOpen?.(opened);
        opened = true;
      };
      socket.onmessage = (event) =>
        callbacks.current.onMessage(JSON.parse(event.data));
      socket.onclose = () => {
        if (disposed) return;
        setStatus("connecting");
        retryTimer = setTimeout(
          connect,
          Math.min(500 * 2 ** attempt++, MAX_RETRY_MS),
        );
      };
    };

    connect();
    return () => {
      disposed = true;
      clearTimeout(retryTimer);
      socket?.close();
    };
  }, [path]);

  return status;
}
