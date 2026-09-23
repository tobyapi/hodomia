import type { WorkspaceModel } from "../workspace/useWorkspace";

export function AnalysisStart({ model }: { model: WorkspaceModel }) {
  const { snapshot, runtime, guarded, locked, start } = model;
  return <><button className="primary full" disabled={!snapshot || !runtime?.ready || !runtime?.chordMiniReady || locked} onClick={() => void guarded(() => start())}>{snapshot?.project.currentRun ? "全体を再分析" : "分析を開始"}</button>
    <ChordSetup model={model} />
    {snapshot?.project.currentRun && <p className="muted">再分析しても手動修正は保持します。</p>}</>;
}

function ChordSetup({ model }: { model: WorkspaceModel }) {
  const { runtime, desktop, locked, guarded, api, setJob, previousRunning, setShowLog } = model;
  return <>{!runtime?.chordMiniReady && desktop && runtime?.analysisSupported !== false && <div className="event-note"><p className="muted">コード分析にはBTCモデルの準備が必要です。</p><button disabled={!runtime?.ready || locked} onClick={() => void guarded(async () => { await api.setupRuntime(true); setJob({ running: true, kind: "setup", log: "" }); previousRunning.current = true; setShowLog(true); })}>コードモデルをセットアップ</button></div>}</>;
}
