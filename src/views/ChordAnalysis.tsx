import type { WorkspaceModel } from "../workspace/useWorkspace";

import { ChordControls } from "../components/ChordControls";

export function ChordAnalysis({ model }: { model: WorkspaceModel }) {
  const { snapshot, runtime, guarded, track, locked, start } = model;
  if (!snapshot) return null;
  return <>{track === "chords" && <ChordControls analysis={snapshot.result}
    ready={!!runtime?.chordMiniReady} locked={!runtime?.ready || locked} onAnalyze={() => void guarded(() => start(undefined, "harmony"))} />}</>;
}
