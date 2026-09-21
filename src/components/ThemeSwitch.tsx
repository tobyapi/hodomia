import { useLayoutEffect, useState } from "react";

type Theme = "dark" | "light";
const STORAGE_KEY = "hodomia.theme";

function readTheme(): Theme {
  try {
    if (window.localStorage.getItem(STORAGE_KEY) === "light") return "light";
  } catch { /* Theme controls remain usable when preference storage is denied. */ }
  return "dark";
}

export function ThemeSwitch() {
  const [theme, setTheme] = useState<Theme>(readTheme);
  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { window.localStorage.setItem(STORAGE_KEY, theme); }
    catch { /* A failed preference write must not block a theme change. */ }
  }, [theme]);

  return <div className="theme-switch" role="group" aria-label="表示テーマ">
    <button type="button" aria-pressed={theme === "light"} onClick={() => setTheme("light")}>
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" /></svg>
      ライト
    </button>
    <button type="button" aria-pressed={theme === "dark"} onClick={() => setTheme("dark")}>
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z" /></svg>
      ダーク
    </button>
  </div>;
}
