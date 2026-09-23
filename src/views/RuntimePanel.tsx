import type { WorkspaceModel } from "../workspace/useWorkspace";
import type { RuntimeStatus } from "../types";

function deviceLabel(runtime: RuntimeStatus | null) {
  if (runtime?.details?.cudaAvailable) return "GPU / CUDA";
  return runtime?.ready ? "CPU" : "初回のみダウンロードが必要です";
}

export function RuntimePanel({ model }: { model: WorkspaceModel }) {
  const { runtime, setJob, showLog, setShowLog, previousRunning, guarded, locked, desktop, api } = model;
  if (runtime?.analysisSupported === false) {
    return <div className="runtime-box"><span>ローカル環境</span>
      <small>この環境では音源解析を利用できません。</small>
      <p className="muted">Windows x64 または Apple Silicon 搭載 Mac をご利用ください。</p>
    </div>;
  }
  return <div className="runtime-box"><span>ローカル環境</span>
    <small>{deviceLabel(runtime)}</small>
    <button disabled={!desktop || locked} onClick={() => void guarded(async () => { await api.setupRuntime(); setJob({ running: true, kind: "setup", log: "" }); previousRunning.current = true; setShowLog(true); })}>{runtime?.ready ? "環境を再確認・修復" : "初回セットアップ"}</button>
    {!runtime?.ready && <small>セットアップ前にuvとGitを用意してください。モデルの取得にはネット接続と数十GBの空き容量が必要です。</small>}
    <button className="text-button" onClick={() => setShowLog(!showLog)}>処理ログ {showLog ? "を閉じる" : "を表示"}</button>
  </div>;
}
