import type { WorkspaceModel } from "../workspace/useWorkspace";
import { ThemeSwitch } from "../components/ThemeSwitch";
import type { RuntimeStatus } from "../types";

function badgeText(runtime: RuntimeStatus | null, desktop: boolean) {
  if (!desktop) return "ブラウザープレビュー";
  if (runtime?.analysisSupported === false) return "○ この環境では解析未対応";
  return runtime?.ready ? "● ローカル解析 準備完了" : "○ 解析環境 未準備";
}

export function Header({ model }: { model: WorkspaceModel }) {
  const { runtime, guarded, locked, desktop, open } = model;
  const unavailable = !desktop || locked || runtime?.analysisSupported === false;
  return <><header className="app-header">
    <div className="brand"><span className="brand-mark">h</span><div><strong>hodomia</strong><small>音を読み解き、映像へ。</small></div></div>
    <div className="header-actions"><ThemeSwitch /><span className={"runtime-badge " + (runtime?.ready ? "ready" : "")}>{badgeText(runtime, desktop)}</span>
      <button disabled={unavailable} onClick={() => void guarded(() => open(false))}>プロジェクトを開く</button>
      <button className="primary" disabled={unavailable} onClick={() => void guarded(() => open(true))}>＋ 曲を読み込む</button></div>
  </header></>;
}
