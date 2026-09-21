import type { WorkspaceModel } from "../workspace/useWorkspace";

export function VocalNotice({ model }: { model: WorkspaceModel }) {
  const { snapshot, track } = model;
  if (!snapshot) return null;
  return <>{track === "vocalEvents" && <p className="muted event-note">{snapshot.result.engines?.vocalEvents ? "検出結果は候補です。通常の歌唱や楽器との取り違え、短い息の見逃しがあります。" : "声の表現はまだ検出していません。「声の表現だけ検出」で追加できます。"} 歌詞と重なる候補も表示します。「あー」「うー」やスキャットは必要に応じて手動で分類してください。</p>}</>;
}
