import { expect, test, vi } from "vitest";
import type { WorkspaceState } from "./useWorkspaceState";
import { updateJob } from "./useWorkspacePolling";

test("failed setup reports failure and opens its log", async () => {
  const state = {
    previousRunning: { current: true },
    api: { runtimeStatus: vi.fn().mockResolvedValue({ ready: false }) },
    setRuntime: vi.fn(), setError: vi.fn(), setShowLog: vi.fn(), setMessage: vi.fn(),
  } as unknown as WorkspaceState;
  await updateJob(state, { running: false, success: false, kind: "setup", log: "uv missing" }, () => true);
  expect(state.setError).toHaveBeenCalledWith("解析環境のセットアップに失敗しました。処理ログを確認してください。");
  expect(state.setShowLog).toHaveBeenCalledWith(true);
  expect(state.previousRunning.current).toBe(false);
});

test("analysis failure reports the worker error", async () => {
  const state = {
    previousRunning: { current: true },
    api: { runtimeStatus: vi.fn().mockResolvedValue({ ready: true }) },
    setRuntime: vi.fn(), setError: vi.fn(), setShowLog: vi.fn(), setMessage: vi.fn(),
  } as unknown as WorkspaceState;
  await updateJob(state, { running: false, success: false, kind: "analysis", log: "", error: "モデルを読み込めません" }, () => true);
  expect(state.setError).toHaveBeenCalledWith("解析に失敗しました: モデルを読み込めません");
});
