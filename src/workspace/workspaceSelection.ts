import { effectiveBpm } from "../editing";
import type { Snapshot, TimelineRow, Track, Tracks } from "../types";

function missingVocals(base: TimelineRow[], saved?: TimelineRow[]) {
  if (!saved) return [];
  return base.filter(row => {
    if (row.method === "vocal-percussion") {
      return !saved.some(item => item.category === "beatbox" && item.start! <= row.start! && item.end! >= row.end!);
    }
    return (row.category === "rap" || row.category === "spoken") && !saved.some(item => item.category === row.category);
  });
}
export function workspaceSelection(state: {
  snapshot: Snapshot | null; viewAuto: boolean; editor: { tracks: Tracks }; track: Track; selectedId?: string; stem: string;
}) {
  const { snapshot, viewAuto, editor, track, selectedId, stem } = state;
  const duration = snapshot?.project.duration ?? 1;
  const base = snapshot?.result.tracks ?? {};
  const tracks = viewAuto ? base : { ...base, ...editor.tracks };
  const rows = tracks[track] ?? [];
  const displayedBpm = effectiveBpm(tracks.beats ?? []);
  const selected = rows.find(row => row.id === selectedId);
  const missingVocalCategories = missingVocals(base.vocalEvents ?? [], editor.tracks.vocalEvents);
  const source = audioSource(snapshot, stem);
  return { duration, base, tracks, rows, displayedBpm, selected, missingVocalCategories, source };
}
function audioSource(snapshot: Snapshot | null, stem: string) {
  if (!snapshot) return null;
  return stem === "original" ? snapshot.project.audio : snapshot.result.stems?.[stem];
}
