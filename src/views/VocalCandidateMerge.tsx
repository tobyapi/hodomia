import type { WorkspaceModel } from "../workspace/useWorkspace";

export function VocalCandidateMerge({ model }: { model: WorkspaceModel }) {
  const { track, viewAuto, editor, missingVocalCategories, locked } = model;
  return <>{track === "vocalEvents" && !viewAuto && missingVocalCategories.length > 0 && <div className="event-note"><p className="muted">手修正に含まれない分類の自動候補が{missingVocalCategories.length}件あります。現在の修正を保持して追加できます。</p><button disabled={locked} onClick={() => editor.change({ ...editor.tracks, vocalEvents: [...editor.tracks.vocalEvents!, ...missingVocalCategories.map(row => ({ ...row, id: crypto.randomUUID() }))].sort((a, b) => (a.start ?? 0) - (b.start ?? 0)) })}>未追加の声の分類を取り込む</button></div>}</>;
}
