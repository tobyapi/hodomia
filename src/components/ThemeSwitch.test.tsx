import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { ThemeSwitch } from "./ThemeSwitch";

const key = "hodomia.theme";
let preferences: Map<string, string>;
beforeEach(() => {
  preferences = new Map();
  vi.stubGlobal("localStorage", {
    getItem: (name: string) => preferences.get(name) ?? null,
    setItem: (name: string, value: string) => preferences.set(name, value),
  });
});
afterEach(() => { delete document.documentElement.dataset.theme; });

test("switches both themes and restores the saved choice after remount", () => {
  const view = render(<ThemeSwitch />);
  expect(screen.getByRole("button", { name: "ダーク" })).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(screen.getByRole("button", { name: "ライト" }));
  expect(document.documentElement).toHaveAttribute("data-theme", "light");
  expect(preferences.get(key)).toBe("light");
  view.unmount();
  render(<ThemeSwitch />);
  expect(screen.getByRole("button", { name: "ライト" })).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(screen.getByRole("button", { name: "ダーク" }));
  expect(document.documentElement).toHaveAttribute("data-theme", "dark");
  expect(preferences.get(key)).toBe("dark");
});

test("invalid stored values fall back to dark", () => {
  preferences.set(key, "invalid");
  render(<ThemeSwitch />);
  expect(document.documentElement).toHaveAttribute("data-theme", "dark");
});

test("unavailable storage does not prevent theme changes", () => {
  vi.stubGlobal("localStorage", {
    getItem: () => { throw new Error("Storage denied"); },
    setItem: () => { throw new Error("Storage denied"); },
  });
  render(<ThemeSwitch />);
  fireEvent.click(screen.getByRole("button", { name: "ライト" }));
  expect(document.documentElement).toHaveAttribute("data-theme", "light");
  expect(screen.getByRole("button", { name: "ダーク" })).toHaveAttribute("aria-pressed", "false");
});
