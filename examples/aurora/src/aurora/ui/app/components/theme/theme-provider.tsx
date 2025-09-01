// components/theme/theme-provider.tsx
import { useEffect, useState } from "react";

export type Theme = "light" | "dark" | "system";

type Props = {
  defaultTheme?: Theme;
  storageKey?: string;
  children?: React.ReactNode;
};

export function ThemeProvider({
  defaultTheme = "system",
  storageKey = "vite-ui-theme",
  children,
}: Props) {
  const [theme, setTheme] = useState<Theme>(() => {
    // Runs on SSR too — must not access browser APIs
    if (typeof window === "undefined") return defaultTheme;
    try {
      const v = window.localStorage.getItem(storageKey) as Theme | null;
      return v ?? defaultTheme;
    } catch {
      return defaultTheme;
    }
  });

  // Persist on client
  useEffect(() => {
    try {
      window.localStorage.setItem(storageKey, theme);
    } catch {}
  }, [theme, storageKey]);

  // Apply class on client
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("light", "dark");

    const apply = (t: Theme) => {
      if (t === "dark") root.classList.add("dark");
      if (t === "light") root.classList.add("light");
    };

    if (theme === "system") {
      const mql = window.matchMedia("(prefers-color-scheme: dark)");
      apply(mql.matches ? "dark" : "light");
      const onChange = (e: MediaQueryListEvent) =>
        apply(e.matches ? "dark" : "light");
      mql.addEventListener?.("change", onChange);
      return () => mql.removeEventListener?.("change", onChange);
    } else {
      apply(theme);
    }
  }, [theme]);

  return <>{children}</>;
}
