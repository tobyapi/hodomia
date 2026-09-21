import type { TimelineRow, Track } from "../types";

export function InspectorActions({ row, track, onLoop, onDelete, onRegion }: {
  row: TimelineRow; track: Track; onLoop: () => void; onDelete: () => void; onRegion: (language: "ja" | "en") => void;
}) {
  return <><div className="button-row"><button onClick={onLoop} disabled={row.start === null || row.end === null || row.start === row.end}>区間ループ</button><button className="danger" onClick={onDelete}>削除</button></div>
    {track === "lyrics" && row.start !== null && row.end !== null && <div className="section-divider"><p className="muted">この区間を指定言語で再解析</p><div className="button-row"><button onClick={() => onRegion("ja")}>日本語</button><button onClick={() => onRegion("en")}>英語</button></div></div>}</>;
}
