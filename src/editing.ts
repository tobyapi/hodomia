import type { TimelineRow, Track, Tracks } from "./types";

export function effectiveBpm(beats: TimelineRow[]): number | null {
  const times = beats.flatMap(row => row.start === null ? [] : [row.start]).sort((a, b) => a - b);
  const intervals = times.slice(1).map((time, i) => time - times[i]).filter(value => value > 0).sort((a, b) => a - b);
  const middle = Math.floor(intervals.length / 2);
  if (!intervals.length) return null;
  return 60 / (intervals.length % 2 ? intervals[middle] : (intervals[middle - 1] + intervals[middle]) / 2);
}

export function validRow(row: TimelineRow, track: Track, duration: number): string | null {
  if (untimedLyric(row, track)) return null;
  if (!finiteTimes(row))
    return "開始・終了は両方入力してください。";
  if (row.start < 0 || row.end > duration || row.end < row.start || (track !== "beats" && row.end === row.start))
    return "曲の範囲内で、開始より後の終了時刻を指定してください。";
  return null;
}
function untimedLyric(row: TimelineRow, track: Track) {
  return row.start === null && row.end === null && (track === "lyrics" || track === "words");
}
function finiteTimes(row: TimelineRow): row is TimelineRow & { start: number; end: number } {
  return row.start !== null && row.end !== null && Number.isFinite(row.start) && Number.isFinite(row.end);
}
export function replaceRow(tracks: Tracks, base: Tracks, track: Track, row: TimelineRow): Tracks {
  const rows = tracks[track] ?? base[track] ?? [];
  const found = rows.some(r => r.id === row.id);
  return { ...tracks, [track]: found ? rows.map(r => r.id === row.id ? row : r) : [...rows, row] };
}
export function beatGrid(bpm: number, anchor: number, end: number, meter: number): TimelineRow[] {
  if (!validBeatGrid(bpm, anchor, end, meter)) throw new Error("BPMは20〜400、開始位置は曲の範囲内、拍子は1〜12で指定してください。");
  const rows: TimelineRow[] = [];
  for (let index = 0; anchor + index * 60 / bpm < end; index++) {
    const time = anchor + index * 60 / bpm;
    rows.push({ id: "manual-beat-" + index, start: time, end: time, label: index % meter === 0 ? "1" : "拍", reviewed: true });
  }
  return rows;
}
function validBeatGrid(bpm: number, anchor: number, end: number, meter: number) {
  const tempo = Number.isFinite(bpm) && bpm >= 20 && bpm <= 400;
  const start = Number.isFinite(anchor) && anchor >= 0 && anchor < end;
  const signature = Number.isInteger(meter) && meter >= 1 && meter <= 12;
  return [tempo, start, signature].every(Boolean);
}
export function timeLabel(time: number) {
  return Math.floor(time / 60).toString().padStart(2, "0") + ":" + (time % 60).toFixed(2).padStart(5, "0");
}
