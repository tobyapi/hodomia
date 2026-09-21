import type { ReactNode } from "react";
import type { TimelineRow, Track, Tracks } from "../types";
import { TRACK_NAMES, VOCAL_CATEGORIES } from "../types";
import { TimelineRegion } from "./TimelineRegion";

export type LaneRenderer = (label: string, content: ReactNode, key: string) => ReactNode;
function groups(track: Track, rows: TimelineRow[]): [string, TimelineRow[]][] {
  if (track !== "vocalEvents") return [[TRACK_NAMES[track], rows]];
  const result: [string, TimelineRow[]][] = Object.entries(VOCAL_CATEGORIES)
    .filter(([category]) => rows.some(row => (row.category ?? "other") === category))
    .map(([category, name]) => [name, rows.filter(row => (row.category ?? "other") === category)]);
  return result.length ? result : [[TRACK_NAMES[track], []]];
}
export function TrackLanes({ tracks, visible, lane, ...region }: {
  tracks: Tracks; visible: Record<string, boolean>; lane: LaneRenderer;
  duration: number; width: number; selected?: string;
  onSelect: (track: Track, row: TimelineRow) => void; onSeek: (time: number) => void;
}) {
  return <>{(Object.keys(TRACK_NAMES) as Track[]).filter(track => visible[track]).flatMap(track =>
    groups(track, tracks[track] ?? []).map(([name, rows], group) => lane(name,
      rows.filter(row => row.start !== null && row.end !== null).map(row =>
        <TimelineRegion key={row.id} track={track} row={row} {...region} />), track + group)))}</>;
}
