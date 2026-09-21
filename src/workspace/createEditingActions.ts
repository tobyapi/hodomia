import { replaceRow } from "../editing";
import type { TimelineRow } from "../types";
import type { WorkspaceState } from "./useWorkspaceState";

export function createEditingActions(state: WorkspaceState) {
  const { track, setSelectedId, setViewAuto, editor, time, duration, base } = state;
  function changeRow(row: TimelineRow) {
    editor.change(replaceRow(editor.tracks, base, track, row)); setViewAuto(false); setSelectedId(row.id);
  }
  function addRow() {
    const row: TimelineRow = { id: crypto.randomUUID(), start: time, end: track === "beats" ? time : Math.min(duration, time + 3), label: track === "lyrics" ? "歌詞を入力" : track === "vocalEvents" ? "その他の非言語発声" : "新しい項目", reviewed: false, ...(track === "vocalEvents" ? { category: "other" as const } : {}) };
    changeRow(row);
  }
  return { changeRow, addRow };
}
