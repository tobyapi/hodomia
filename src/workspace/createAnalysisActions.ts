import type { AnalysisOptions } from "../types";
import type { WorkspaceState } from "./useWorkspaceState";

export function createAnalysisActions(state: WorkspaceState, save: () => Promise<void>) {
  const { snapshot, setJob, setMessage, previousRunning, mode, lyrics, eventSensitivity, beatboxRecall, setTrack, setSelectedId, setViewAuto, editor, selected, api } = state;
  async function start(region?: AnalysisOptions["region"], scope?: "vocal-events" | "harmony") {
    if (!snapshot) return;
    if (editor.dirty) await save();
    setMessage("解析を開始しています…");
    const started = await api.analyze(snapshot.root, { mode, lyrics: region ? (selected?.label ?? "") : lyrics, eventSensitivity, beatboxRecall, ...(region ? { region } : {}), ...(scope ? { scope } : {}) });
    previousRunning.current = true;
    setJob({ running: true, kind: "analysis", log: "", jobId: started.jobId }); setViewAuto(false);
    if (scope) { setTrack(scope === "harmony" ? "chords" : "vocalEvents"); setSelectedId(undefined); }
  }
  return { start };
}
