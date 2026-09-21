import type { WorkspaceModel } from "../workspace/useWorkspace";

export function DeleteDialog({ model }: { model: WorkspaceModel }) {
  const { snapshot, setSnapshot, setSavedProjects, deleteTarget, setDeleteTarget, setMessage, guarded, editor, setPlaying, audio, locked, api } = model;
  return <>{deleteTarget && <div className="delete-overlay"><section className="delete-dialog" role="dialog" aria-modal="true" aria-label="解析データの削除"><h3>「{deleteTarget.name}」の解析データを削除しますか？</h3><p>解析結果・分離音声・手修正・書き出しデータを削除し、一覧から取り除きます。この操作は元に戻せません。</p><p>元の音源と再生用音声は残します。「プロジェクトを開く」から再登録し、再分析できます。</p><div className="button-row"><button autoFocus disabled={locked} onClick={() => setDeleteTarget(null)}>キャンセル</button><button className="danger" disabled={locked} onClick={() => void guarded(async () => { const root = deleteTarget.root; await api.deleteAnalysis(root); if (snapshot?.root === root) { audio.current?.pause(); setSnapshot(null); editor.reset({}); setPlaying(false); } await api.removeSavedProject(root); setSavedProjects(await api.savedProjects()); setDeleteTarget(null); setMessage("解析データを削除しました。元の音源と再生用音声は残っています。"); })}>解析データを削除</button></div></section></div>}</>;
}
