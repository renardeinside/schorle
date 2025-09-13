// theme.tsx
"use client";
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type Theme = "light" | "dark" | "system";

type Ctx = {
  theme: Theme; // the raw choice
  resolvedTheme: "light" | "dark"; // after resolving 'system'
  setTheme: (t: Theme) => void;
};

const ThemeCtx = createContext<Ctx | null>(null);

export function ThemeProvider({
  children,
  defaultTheme = "system" as Theme,
  storageKey = "theme",
}: {
  children: ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
}) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === "undefined") return defaultTheme;
    return (localStorage.getItem(storageKey) as Theme) || defaultTheme;
  });

  // keep CSS class in sync
  useEffect(() => {
    const root = document.documentElement;
    const mql = window.matchMedia("(prefers-color-scheme: dark)");

    function apply(current: Theme) {
      const next =
        current === "system" ? (mql.matches ? "dark" : "light") : current;
      root.classList.toggle("dark", next === "dark");
    }

    // initial
    apply(theme);

    // react to system changes when on 'system'
    const handle = () => theme === "system" && apply("system");
    mql.addEventListener?.("change", handle);

    // cross-tab sync
    const onStorage = (e: StorageEvent) => {
      if (e.key === storageKey && e.newValue) {
        setThemeState(e.newValue as Theme);
      }
    };
    window.addEventListener("storage", onStorage);

    return () => {
      mql.removeEventListener?.("change", handle);
      window.removeEventListener("storage", onStorage);
    };
  }, [theme]);

  const setTheme = (t: Theme) => {
    try {
      localStorage.setItem(storageKey, t);
    } catch {}
    // avoid transition flash during switch
    const root = document.documentElement;
    root.classList.add("[&_*]:!transition-none");
    setThemeState(t);
    // next frame clear
    requestAnimationFrame(() => {
      requestAnimationFrame(() =>
        root.classList.remove("[&_*]:!transition-none"),
      );
    });
  };

  const resolvedTheme = useMemo<"light" | "dark">(() => {
    if (typeof window === "undefined")
      return theme === "dark" ? "dark" : "light";
    if (theme === "system")
      return window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    return theme;
  }, [theme]);

  const value = useMemo(
    () => ({ theme, resolvedTheme, setTheme }),
    [theme, resolvedTheme],
  );

  return <ThemeCtx.Provider value={value}>{children}</ThemeCtx.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeCtx);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
