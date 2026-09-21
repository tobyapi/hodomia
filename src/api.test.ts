import { expect, test, vi } from "vitest";
import { asset } from "./api";
import { convertFileSrc } from "@tauri-apps/api/core";

vi.mock("@tauri-apps/api/core", () => ({ convertFileSrc: vi.fn((path: string) => path), invoke: vi.fn(), isTauri: vi.fn() }));

test.each([
  [String.raw`\\?\C:\音楽テスト\サンプル曲`, "audio.wav", String.raw`\\?\C:\音楽テスト\サンプル曲\audio.wav`],
  [String.raw`\\?\C:\音楽テスト\サンプル曲`, "runs/first/vocals.wav", String.raw`\\?\C:\音楽テスト\サンプル曲\runs\first\vocals.wav`],
  [String.raw`\\?\UNC\server\音楽` + "\\", "audio.wav", String.raw`\\?\UNC\server\音楽\audio.wav`],
  ["C:/hodomia/曲", "audio.wav", String.raw`C:\hodomia\曲\audio.wav`],
  ["/home/music/曲/", "audio.wav", "/home/music/曲/audio.wav"],
])("audio paths remain valid for %s", (root, relative, expected) => {
  asset(root, relative);
  expect(convertFileSrc).toHaveBeenLastCalledWith(expected);
});
