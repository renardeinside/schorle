import { useMemo } from "react";
import type { Dict } from "./types";

/**
 * useHeaders hook
 * - On the server: reads from globalThis.__SCHORLE_HEADERS__
 * - On the client: reads from injected script tag __SCHORLE_HEADERS__
 */
export function useHeaders(): Dict {
  return useMemo(() => {
    if (typeof window === "undefined") {
      // Server-side
      const raw = (globalThis as any).__SCHORLE_HEADERS__ as
        | Record<string, string>
        | undefined;
      return raw ? { ...raw } : {};
    } else {
      // Client-side - read from injected script tag
      try {
        const scriptEl = document.getElementById("__SCHORLE_HEADERS__");
        if (scriptEl && scriptEl.textContent) {
          const parsed = JSON.parse(scriptEl.textContent);
          return parsed || {};
        }
      } catch (e) {
        console.warn("Failed to parse headers from script tag:", e);
      }
      return {};
    }
  }, []);
}
