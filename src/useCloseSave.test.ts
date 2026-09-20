import { act, renderHook } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { readFileSync } from "node:fs";
import { useCloseSave } from "./useCloseSave";

const native = vi.hoisted(() => ({
  desktop: true,
  handler: undefined as undefined | ((event: { preventDefault: () => void }) => Promise<void>),
  destroy: vi.fn(),
  unlisten: vi.fn(),
}));
vi.mock("@tauri-apps/api/core", () => ({ isTauri: () => native.desktop }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({
  destroy: native.destroy,
  onCloseRequested: async (handler: typeof native.handler) => { native.handler = handler; return native.unlisten; },
}) }));
beforeEach(() => {
  vi.resetAllMocks(); native.desktop = true; native.handler = undefined;
  native.destroy.mockResolvedValue(undefined);
});
async function requestClose() {
  const preventDefault = vi.fn();
  await act(async () => { await native.handler!({ preventDefault }); });
  expect(preventDefault).toHaveBeenCalledOnce();
}
test("clean window closes without saving and has the required native permission", async () => {
  const save = vi.fn();
  renderHook(() => useCloseSave(false, save, vi.fn()));
  await requestClose();
  expect(save).not.toHaveBeenCalled();
  expect(native.destroy).toHaveBeenCalledOnce();
  const capability = JSON.parse(readFileSync("src-tauri/capabilities/default.json", "utf8"));
  expect(capability.windows).toContain("main");
  expect(capability.permissions).toContain("core:window:allow-destroy");
});
test("dirty window waits for save and suppresses repeated close requests", async () => {
  let finish!: () => void;
  const save = vi.fn(() => new Promise<void>(resolve => { finish = resolve; }));
  renderHook(() => useCloseSave(true, save, vi.fn()));
  const first = native.handler!({ preventDefault: vi.fn() });
  await requestClose();
  expect(save).toHaveBeenCalledOnce();
  expect(native.destroy).not.toHaveBeenCalled();
  await act(async () => { finish(); await first; });
  expect(native.destroy).toHaveBeenCalledOnce();
});
test("failed save keeps the window open and permits retry", async () => {
  const save = vi.fn().mockRejectedValueOnce(new Error("保存失敗")).mockResolvedValue(undefined);
  const error = vi.fn();
  renderHook(() => useCloseSave(true, save, error));
  await requestClose();
  expect(native.destroy).not.toHaveBeenCalled();
  expect(error).toHaveBeenCalledWith(expect.stringContaining("保存失敗"));
  await requestClose();
  expect(native.destroy).toHaveBeenCalledOnce();
});
test("destroy errors are visible instead of leaving an unhandled rejection", async () => {
  native.destroy.mockRejectedValueOnce(new Error("権限エラー"));
  const error = vi.fn();
  renderHook(() => useCloseSave(false, vi.fn(), error));
  await requestClose();
  expect(error).toHaveBeenCalledWith(expect.stringContaining("権限エラー"));
});
