import { useMemo } from "react";
import type { Dict } from "./types";

/**
 * Parse cookies from a cookie string into a dictionary
 */
function parseCookies(cookieStr: string | null | undefined): Dict {
  if (!cookieStr) return {};
  return cookieStr
    .split(";")
    .map((c) => c.trim().split("="))
    .reduce<Dict>((acc, [k, ...v]) => {
      if (!k) return acc;
      acc[k] = decodeURIComponent(v.join("="));
      return acc;
    }, {});
}

/**
 * useCookies hook
 * - On the server: reads from globalThis.__SCHORLE_COOKIES__
 * - On the client: reads from injected script tag __SCHORLE_COOKIES__, falls back to document.cookie
 */
export function useCookies(): Dict {
  return useMemo(() => {
    if (typeof window === "undefined") {
      // Server-side
      const raw = (globalThis as any).__SCHORLE_COOKIES__ as
        | string
        | Dict
        | undefined;
      if (!raw) return {};
      if (typeof raw === "string") return parseCookies(raw);
      return { ...raw };
    } else {
      // Client-side - first try injected script tag for SSR consistency
      try {
        const scriptEl = document.getElementById("__SCHORLE_COOKIES__");
        if (scriptEl && scriptEl.textContent) {
          const parsed = JSON.parse(scriptEl.textContent);
          return parsed || {};
        }
      } catch (e) {
        console.warn("Failed to parse cookies from script tag:", e);
      }

      // Fallback to document.cookie for client-only behavior
      return parseCookies(document.cookie);
    }
  }, []);
}
