import type { WorkspaceModel } from "../workspace/useWorkspace";

export function RuntimePanel({ model }: { model: WorkspaceModel }) {
  const { runtime, setJob, showLog, setShowLog, previousRunning, guarded, locked, desktop, api } = model;
  return <><div className="runtime-box"><span>ローカル環境</span><small>{runtime?.details?.cudaAvailable ? "GPU / CUDA" : runtime?.ready ? "CPU" : "初回のみダウンロードが必要です"}</small>
    <button disabled={!desktop || locked} onClick={() => void guarded(async () => { await api.setupRuntime(); setJob({ running: true, kind: "setup", log: "" }); previousRunning.current = true; setShowLog(true); })}>{runtime?.ready ? "環境を再確認・修復" : "初回セットアップ"}</button>
    <button className="text-button" onClick={() => setShowLog(!showLog)}>処理ログ {showLog ? "を閉じる" : "を表示"}</button>
  </div></>;
}
