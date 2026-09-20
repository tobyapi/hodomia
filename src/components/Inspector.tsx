import { useState } from "react";
import { timeLabel, validRow } from "../editing";
import type { TimelineRow, Track, VocalCategory } from "../types";
import { TRACK_NAMES, VOCAL_CATEGORIES, STEM_NAMES } from "../types";

export function Inspector({ track, row, duration, onSave, onDelete, onLoop, onRegion }: {
  track: Track; row: TimelineRow; duration: number; onSave: (row: TimelineRow) => void;
  onDelete: () => void; onLoop: () => void; onRegion: (language: "ja" | "en") => void;
}) {
  const [label, setLabel] = useState(row.label);
  const [category, setCategory] = useState<VocalCategory>(row.category ?? "other");
  const [start, setStart] = useState(row.start?.toString() ?? "");
  const [end, setEnd] = useState(row.end?.toString() ?? "");
  const [reviewed, setReviewed] = useState(row.reviewed ?? false);
  const [error, setError] = useState("");
  const save = () => {
    const value = { ...row, label, start: start === "" ? null : Number(start), end: end === "" ? null : Number(end), reviewed, ...(track === "vocalEvents" ? { category } : {}) };
    const problem = validRow(value, track, duration);
    if (problem) { setError(problem); return; }
    onSave(value); setError("");
  };
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
    {track === "vocalEvents" && row.score !== undefined && <div className="event-evidence"><p>元の推定：{VOCAL_CATEGORIES[row.detectedCategory ?? row.category ?? "other"]}</p><p>モデルスコア {row.score.toFixed(3)}（正解率ではありません）</p><p>参照音声：{row.evidenceSources?.map(s => s === "original" ? "原曲" : STEM_NAMES[s] ?? s).join("・")}</p><p className="muted">「あー」「うー」やスキャットを含め、歌唱との区別が難しい声は手動で分類できます。</p></div>}
    {error && <p role="alert" className="error">{error}</p>}
    <button className="primary" onClick={save}>変更を適用</button>
    <div className="button-row"><button onClick={onLoop} disabled={row.start === null || row.end === null || row.start === row.end}>区間ループ</button><button className="danger" onClick={onDelete}>削除</button></div>
    {track === "lyrics" && row.start !== null && row.end !== null && <div className="section-divider"><p className="muted">この区間を指定言語で再解析</p><div className="button-row"><button onClick={() => onRegion("ja")}>日本語</button><button onClick={() => onRegion("en")}>英語</button></div></div>}
  </section>;
}
