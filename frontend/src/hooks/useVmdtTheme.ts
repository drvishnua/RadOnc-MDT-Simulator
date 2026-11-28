import { useCallback, useEffect, useState } from "react";
import type { ResolvedTheme, ThemeMode } from "../virtualMdtTypes.js";

function readSystemScheme(): ResolvedTheme {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function readStoredMode(): ThemeMode {
  try {
    const val = window.localStorage.getItem("color-scheme");
    if (val === "light" || val === "dark") return val;
  } catch {
    // ignore storage restriction
  }
  return "system";
}

export function useVmdtTheme() {
  const [themeMode, setThemeModeState] = useState<ThemeMode>(readStoredMode);
  const [systemScheme, setSystemScheme] = useState<ResolvedTheme>(readSystemScheme);

  const resolvedTheme: ResolvedTheme = themeMode === "system" ? systemScheme : themeMode;

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e: MediaQueryListEvent) => {
      setSystemScheme(e.matches ? "dark" : "light");
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === "color-scheme") {
        setThemeModeState(readStoredMode());
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  useEffect(() => {
    const meta = document.querySelector('meta[name="color-scheme"]');
    if (meta) {
      meta.setAttribute("content", themeMode === "system" ? "light dark" : themeMode);
    }
    document.documentElement.classList.toggle("dark", resolvedTheme === "dark");
  }, [themeMode, resolvedTheme]);

  const setThemeMode = useCallback((next: ThemeMode) => {
    try {
      if (next === "system") {
        window.localStorage.removeItem("color-scheme");
      } else {
        window.localStorage.setItem("color-scheme", next);
      }
    } catch {
      // ignore storage restriction
    }
    setThemeModeState(next);
  }, []);

  const toggleTheme = useCallback(() => {
    const target: ResolvedTheme = resolvedTheme === "dark" ? "light" : "dark";
    if (target === systemScheme) {
      try {
        window.localStorage.removeItem("color-scheme");
      } catch {
        // ignore
      }
      setThemeModeState("system");
    } else {
      try {
        window.localStorage.setItem("color-scheme", target);
      } catch {
        // ignore
      }
      setThemeModeState(target);
    }
  }, [resolvedTheme, systemScheme]);

  return { themeMode, resolvedTheme, setThemeMode, toggleTheme };
}

export default useVmdtTheme;
