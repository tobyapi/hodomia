import type { WorkspaceModel } from "../workspace/useWorkspace";

import type { Track } from "../types";
import { TRACK_NAMES } from "../types";

export function EditorToolbar({ model }: { model: WorkspaceModel }) {
  const { busy, track, setTrack, setSelectedId, viewAuto, setViewAuto, editor, rows, addRow } = model;
  return <><div className="editor-toolbar"><select aria-label="編集トラック" value={track} onChange={e => { setTrack(e.target.value as Track); setSelectedId(undefined); }}>{Object.entries(TRACK_NAMES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select>
    <button disabled={viewAuto || busy} onClick={addRow}>＋ 再生位置に追加</button><label className="check-label"><input type="checkbox" checked={viewAuto} onChange={e => setViewAuto(e.target.checked)} />自動結果を比較</label>
    {editor.tracks[track] && <button disabled={busy} onClick={() => { const next = { ...editor.tracks }; delete next[track]; editor.change(next); setViewAuto(false); }}>このトラックを自動結果へ戻す</button>}<span className="muted">{rows.length} 項目</span></div></>;
}
