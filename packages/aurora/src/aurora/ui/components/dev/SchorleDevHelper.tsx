"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Status = "connecting" | "connected" | "reconnecting" | "offline";

function devIndicatorUrl() {
  const { protocol, host } = window.location;
  return (
    (protocol === "https:" ? "wss:" : "ws:") +
    "//" +
    host +
    "/_schorle/dev-indicator"
  );
}

export default function SchorleLiveIndicator() {
  if (process.env.NODE_ENV === "production") {
    return null;
  }

  const [status, setStatus] = useState<Status>("connecting");
  const [lastPing, setLastPing] = useState<number | null>(null);

  const prevStatusRef = useRef<Status>("connecting");

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const unmountedRef = useRef(false);
  const everConnectedRef = useRef(false);

  const label = useMemo(() => {
    switch (status) {
      case "connected":
        return "Connected";
      case "reconnecting":
        return "Reconnecting…";
      case "offline":
        return "Offline";
      default:
        return "Connecting…";
    }
  }, [status]);

  // trigger a brief flash whenever status changes
  useEffect(() => {
    if (prevStatusRef.current !== status) {
      prevStatusRef.current = status;
    }
  }, [status]);

  useEffect(() => {
    unmountedRef.current = false;
    let attempt = 0;

    const clearTimer = () => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };

    const scheduleReconnect = () => {
      if (unmountedRef.current) return;
      setStatus(everConnectedRef.current ? "reconnecting" : "connecting");
      attempt += 1;
      const waitMs = Math.min(5000, 300 * Math.pow(2, Math.min(attempt, 4)));
      clearTimer();
      reconnectTimerRef.current = window.setTimeout(open, waitMs);
    };

    const open = () => {
      if (unmountedRef.current) return;
      try {
        const ws = new WebSocket(devIndicatorUrl());
        wsRef.current = ws;

        ws.onopen = () => {
          setStatus("connected");
          attempt = 0;
          if (everConnectedRef.current) {
            setTimeout(() => window.location.reload(), 80);
          } else {
            everConnectedRef.current = true;
          }
        };

        ws.onmessage = (evt) => {
          setLastPing(Date.now());
          try {
            const data = JSON.parse(String(evt.data ?? "{}"));
            if (data && data.type === "reload") {
              // Prefetch current page to warm caches, then hard reload
              const href = window.location.href;
              fetch(href, { cache: "no-store" }).finally(() => {
                window.location.reload();
              });
            }
          } catch {
            // ignore non-JSON pings
          }
        };
        ws.onerror = () => {
          /* onclose will handle retry */
        };
        ws.onclose = () => {
          setStatus("offline");
          scheduleReconnect();
        };
      } catch {
        scheduleReconnect();
      }
    };

    open();

    return () => {
      unmountedRef.current = true;
      clearTimer();
      try {
        wsRef.current?.close();
      } catch {}
      wsRef.current = null;
    };
  }, []);

  // dynamic styling helpers
  const dotColor =
    status === "connected"
      ? "bg-green-500"
      : status === "reconnecting"
        ? "bg-yellow-500"
        : status === "offline"
          ? "bg-red-500"
          : "bg-gray-400";

  return (
    <div className="fixed right-3 bottom-3 z-[9999] select-none pointer-events-none">
      <div
        className={[
          "flex items-center gap-2 rounded-full border bg-white/85 dark:bg-black/60 backdrop-blur px-3 py-1 shadow-md pointer-events-auto",
          // smooth transitions for border/background/ring
          "transition-all duration-300",
        ].join(" ")}
      >
        <span
          className={[
            "inline-block h-2.5 w-2.5 rounded-full",
            dotColor,
            // smooth color & scale transition
            "transition-all duration-300",
            // subtle pop on change; pulse while reconnecting/connecting
            status === "reconnecting" || status === "connecting"
              ? "motion-safe:animate-pulse"
              : "",
          ].join(" ")}
        />
        <span
          className={[
            "text-xs text-gray-700 dark:text-gray-200",
            "transition-opacity duration-200",
            "min-w-[75px] text-left",
            status === "offline" ? "opacity-90" : "opacity-100",
          ].join(" ")}
        >
          {label}
        </span>
        <span
          className={[
            "text-[10px] text-gray-500 min-w-[20px] tabular-nums",
            "transition-opacity duration-200",
            lastPing ? "opacity-70" : "opacity-0",
          ].join(" ")}
        >
          {lastPing
            ? `${Math.max(0, Math.round((Date.now() - lastPing) / 1000))}s`
            : null}
        </span>
      </div>
    </div>
  );
}
