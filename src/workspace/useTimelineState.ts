import { useState } from "react";
import type { Track } from "../types";
import { useEdits } from "../useEdits";
const INITIAL_VISIBLE: Record<string, boolean> = { beats: true, sections: true, lyrics: true, words: false, vocalEvents: true, chords: true, key: false, energy: true, pitch: true, stems: false };

export function useTimelineState() {
  const [track, setTrack] = useState<Track>("sections");
  const [selectedId, setSelectedId] = useState<string>();
  const [visible, setVisible] = useState(INITIAL_VISIBLE);
  const [zoom, setZoom] = useState(8);
  const [bpm, setBpm] = useState("120");
  const [anchor, setAnchor] = useState("0");
  const [meter, setMeter] = useState("4");
  const [viewAuto, setViewAuto] = useState(false);
  const [draftDirty, setDraftDirty] = useState(false);
  const editor = useEdits();
  return { track, setTrack, selectedId, setSelectedId, visible, setVisible, zoom, setZoom, bpm, setBpm, anchor, setAnchor, meter, setMeter, viewAuto, setViewAuto, draftDirty, setDraftDirty, editor };
}
