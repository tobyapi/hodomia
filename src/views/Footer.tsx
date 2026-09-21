import type { WorkspaceModel } from "../workspace/useWorkspace";

export function Footer({ model }: { model: WorkspaceModel }) {
  const { snapshot, editor } = model;
  if (!snapshot) return null;
  return <><footer><span>LOCAL FIRST · 音源は外部へ送信しません</span><span>{snapshot ? snapshot.root : "Music Sweeper"}{editor.dirty ? " · 未保存の変更あり" : ""}</span></footer></>;
}
