import type { WorkspaceModel } from "../workspace/useWorkspace";

export function Header({ model }: { model: WorkspaceModel }) {
  const { runtime, guarded, locked, desktop, open } = model;
  return <><header className="app-header">
    <div className="brand"><span className="brand-mark">M</span><div><strong>Music Sweeper</strong><small>音を読み解き、映像へ。</small></div></div>
    <div className="header-actions"><span className={"runtime-badge " + (runtime?.ready ? "ready" : "")}>{runtime?.ready ? "● ローカル解析 準備完了" : desktop ? "○ 解析環境 未準備" : "ブラウザープレビュー"}</span>
      <button disabled={!desktop || locked} onClick={() => void guarded(() => open(false))}>プロジェクトを開く</button>
      <button className="primary" disabled={!desktop || locked} onClick={() => void guarded(() => open(true))}>＋ 曲を読み込む</button></div>
  </header></>;
}
