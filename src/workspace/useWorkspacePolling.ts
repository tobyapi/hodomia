import { useEffect } from "react";
import type { Job, Snapshot } from "../types";
import { pollProject } from "./pollProject";
import { pollUiRequest } from "./pollUiRequest";
import type { WorkspaceState } from "./useWorkspaceState";

async function updateJob(state: WorkspaceState, next: Job, alive: () => boolean) {
  if (state.previousRunning.current && !next.running) {
    const info = await state.api.runtimeStatus();
    if (alive()) state.setRuntime(info);
    if (next.success === false && alive()) state.setError("処理が終了しました。ログと解析状態を確認してください。");
  }
  state.previousRunning.current = next.running;
}
function startPolling(state: WorkspaceState, install: (value: Snapshot) => void) {
  let alive = true, polling = false;
  const isAlive = () => alive;
  async function refresh() {
    if (polling) return;
    polling = true;
    try {
      const next = await state.api.jobStatus();
      if (!alive) return;
      state.setJob(next);
      await pollProject(state, isAlive);
      if (!alive) return;
      await updateJob(state, next, isAlive);
      if (!state.busy && !state.editor.dirty && !state.draftDirty && !next.running) {
        await pollUiRequest(state, install, isAlive);
      }
    } catch (error) { if (alive) state.setError(String(error)); } finally { polling = false; }
  }
  const timer = window.setInterval(refresh, 1800);
  void refresh();
  return () => { alive = false; window.clearInterval(timer); };
}
export function useWorkspacePolling(state: WorkspaceState, install: (value: Snapshot) => void) {
  const { api, snapshot, editor, draftDirty, busy, stem, setRuntime, setSavedProjects, setError } = state;
  useEffect(() => {
    if (!api.desktop()) return;
    api.runtimeStatus().then(setRuntime).catch(error => setError(String(error)));
    api.savedProjects().then(setSavedProjects).catch(error => setError("保存した曲を取得できません: " + String(error)));
  }, []);
  useEffect(() => {
    if (!api.desktop()) return;
    return startPolling(state, install);
  }, [snapshot?.root, snapshot?.edits.revision, editor.dirty, draftDirty, busy, stem]);
}
