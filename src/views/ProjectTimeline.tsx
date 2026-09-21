import type { WorkspaceModel } from "../workspace/useWorkspace";

import { Timeline } from "../components/Timeline";

export function ProjectTimeline({ model }: { model: WorkspaceModel }) {
  const { snapshot, setTrack, selectedId, setSelectedId, visible, zoom, time, duration, tracks, seek } = model;
  if (!snapshot) return null;
  return <><Timeline duration={duration} time={time} zoom={zoom} tracks={tracks} analysis={snapshot.result} visible={visible} selected={selectedId} onSeek={seek} onSelect={(t, row) => { setTrack(t); setSelectedId(row.id); }} /></>;
}
