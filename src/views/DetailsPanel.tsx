import type { WorkspaceModel } from "../workspace/useWorkspace";

import { Inspector } from "../components/Inspector";

export function DetailsPanel({ model }: { model: WorkspaceModel }) {
  const { guarded, track, setSelectedId, viewAuto, setDraftDirty, editor, setLoop, duration, rows, selected, start, changeRow, seek } = model;
  return <><aside className="inspector"><div className="eyebrow">DETAILS</div>
    {selected && !viewAuto ? <Inspector key={selected.id + JSON.stringify(selected)} track={track} row={selected} duration={duration} onDirtyChange={setDraftDirty} onSave={changeRow} onDelete={() => { editor.change({ ...editor.tracks, [track]: rows.filter(r => r.id !== selected.id) }); setSelectedId(undefined); }} onLoop={() => { if (selected.start !== null && selected.end !== null) { setLoop({ start: selected.start, end: selected.end }); seek(selected.start); } }} onRegion={language => { if (selected.start !== null && selected.end !== null) void guarded(() => start({ start: selected.start!, end: selected.end!, language })); }} /> :
      <div className="inspector-empty"><span>⌁</span><h3>{viewAuto ? "自動結果を比較中" : "気になる区間を選択"}</h3><p>タイムラインや一覧から項目を選ぶと、内容と時刻を修正できます。</p><p>未確認の推定は、試聴して確かめてください。</p></div>}
  </aside></>;
}
