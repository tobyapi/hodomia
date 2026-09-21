import type { WorkspaceModel } from "../workspace/useWorkspace";

export function ExternalChanges({ model }: { model: WorkspaceModel }) {
  const { snapshot, externalChange, guarded, api, install } = model;
  if (!snapshot) return null;
  return <>{externalChange && <div role="alert" className="error">AIまたは別の画面で保存内容が更新されました。手元の変更は保持しています。
    <button onClick={() => { if (window.confirm("手元の未保存の変更を破棄し、最新の保存内容を読み込みますか？")) void guarded(async () => install(await api.openProject(snapshot.root))); }}>最新の保存内容を読み込む</button>
  </div>}</>;
}
