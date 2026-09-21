import { timeLabel } from "../editing";
import type { TimelineRow, Track } from "../types";

function shape(track: Track, row: TimelineRow) {
  if (track !== "beats") return { y: 15, height: 45, rx: 4 };
  return { y: row.label === "1" ? 8 : 27, height: row.label === "1" ? 58 : 39, rx: 0 };
}
export function TimelineRegion({ track, row, width, duration, selected, onSelect, onSeek }: {
  track: Track; row: TimelineRow; width: number; duration: number; selected?: string;
  onSelect: (track: Track, row: TimelineRow) => void; onSeek: (time: number) => void;
}) {
  const x = row.start! / duration * width;
  const w = Math.max(track === "beats" ? 2 : 5, (row.end! - row.start!) / duration * width);
  const select = () => { onSelect(track, row); onSeek(row.start!); };
  const label = row.label + (row.uncertain ? " ?" : "");
  return <g className={"region " + track + (selected === row.id ? " selected" : "")}
    onClick={e => { e.stopPropagation(); select(); }} role="button" tabIndex={0}
    aria-label={row.label + " " + timeLabel(row.start!)} onKeyDown={e => { if (e.key === "Enter") select(); }}>
    <title>{row.label}{row.uncertain ? "（候補）" : ""} · {row.warning ?? ""}</title>
    <rect x={x} width={w} {...shape(track, row)} />
    {track !== "beats" && w > 22 && <text x={x + 7} y={43}>{label.slice(0, Math.max(1, Math.floor(w / 12) - 1))}</text>}
  </g>;
}
