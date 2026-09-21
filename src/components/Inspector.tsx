import { timeLabel } from "../editing";
import type { TimelineRow, Track, VocalCategory } from "../types";
import { TRACK_NAMES, VOCAL_CATEGORIES } from "../types";
import { EventEvidence } from "./EventEvidence";
import { InspectorActions } from "./InspectorActions";
import { useInspectorDraft } from "./useInspectorDraft";

export function Inspector({ track, row, duration, onSave, onDelete, onLoop, onRegion, onDirtyChange }: {
  track: Track; row: TimelineRow; duration: number; onSave: (row: TimelineRow) => void;
  onDelete: () => void; onLoop: () => void; onRegion: (language: "ja" | "en") => void;
  onDirtyChange?: (dirty: boolean) => void;
}) {
  const { label, category, start, end, reviewed, error, save, setLabel, setCategory, setStart, setEnd, setReviewed } =
    useInspectorDraft(row, track, duration, onSave, onDirtyChange);
  return <section className="inspector-form">
    <div className="eyebrow">{TRACK_NAMES[track]} / EDIT</div>
    <h3>{row.start === null ? "時刻未確定" : timeLabel(row.start)}</h3>
    {track === "vocalEvents" && <label>声の分類<select value={category} onChange={e => { const value = e.target.value as VocalCategory; setCategory(value); if (Object.values(VOCAL_CATEGORIES).includes(label)) setLabel(VOCAL_CATEGORIES[value]); }}>{Object.entries(VOCAL_CATEGORIES).map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></label>}
    <label>内容<textarea value={label} onChange={e => setLabel(e.target.value)} rows={3} /></label>
    {track === "vocalEvents" && <p className="muted">声の種類と区間の候補です。ラップと朗読・語りは重複する場合があります。言葉の文字起こしは歌詞トラックで確認してください。非言語音は「ブッ・ツク」「んー」「［息］」などを内容に手入力できます。分類を変えても入力した表記は保持します。JSON/CSVに保存されます。</p>}
    <div className="field-pair"><label>開始（秒）<input type="number" step=".01" value={start} onChange={e => { setStart(e.target.value); if (track === "beats") setEnd(e.target.value); }} /></label>
      <label>終了（秒）<input type="number" step=".01" disabled={track === "beats"} value={end} onChange={e => setEnd(e.target.value)} /></label></div>
    <label className="check-label"><input type="checkbox" checked={reviewed} onChange={e => setReviewed(e.target.checked)} />試聴して確認済み</label>
    {row.warning && <p className="muted">{row.warning}</p>}
    {track === "chords" && row.uncertain && <p className="muted">このコードは確度の低い候補です。和音名を確認・修正してください。</p>}
    {track === "vocalEvents" && <EventEvidence row={row} />}
    {error && <p role="alert" className="error">{error}</p>}
    <button className="primary" onClick={save}>変更を適用</button>
    <InspectorActions row={row} track={track} onLoop={onLoop} onDelete={onDelete} onRegion={onRegion} />
  </section>;
}
