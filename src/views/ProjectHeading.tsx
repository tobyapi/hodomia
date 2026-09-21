import { timeLabel } from "../editing";
import type { WorkspaceModel } from "../workspace/useWorkspace";

export function ProjectHeading({ model }: { model: WorkspaceModel }) {
  const { snapshot, job, busy, setMessage, guarded, editor, api, save } = model;
  if (!snapshot) return null;
  return <><div className="project-heading"><SongSummary model={model} />
    <div className="button-row"><button disabled={!editor.canUndo || busy} onClick={editor.undo}>元に戻す</button><button disabled={!editor.canRedo || busy} onClick={editor.redo}>やり直す</button><button disabled={!editor.dirty || busy} onClick={() => void guarded(save)}>{editor.dirty ? "● 修正を保存" : "保存済み"}</button>
      <button disabled={busy || job.running} onClick={() => void guarded(async () => { if (editor.dirty) await save(); const result = await api.exportProject(snapshot.root); setMessage("書き出しました: " + result.path + (result.untimedLyrics ? "（時刻未確定の歌詞は字幕から除外）" : "")); })}>書き出し ↗</button></div>
  </div></>;
}

function SongSummary({ model }: { model: WorkspaceModel }) {
  const { snapshot, duration, displayedBpm, editor, viewAuto, tracks } = model;
  if (!snapshot) return null;
  return <div><div className="eyebrow">SONG WORKSPACE</div><h1>{snapshot.project.name}</h1><p className="muted">{timeLabel(duration)} · {displayedBpm ? displayedBpm.toFixed(1) + (editor.tracks.beats && !viewAuto ? " BPM（修正）" : " BPM（推定）") : "BPM 未解析"} · {(tracks.key ?? [])[0]?.label ?? "キー 未解析"}</p></div>;
}
