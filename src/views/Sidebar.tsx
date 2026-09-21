import type { WorkspaceModel } from "../workspace/useWorkspace";

import { AnalysisSettings } from "./AnalysisSettings";
import { AnalysisStart } from "./AnalysisStart";
import { CancelJob } from "./CancelJob";
import { RuntimePanel } from "./RuntimePanel";
import { SavedProjects } from "./SavedProjects";
import { TrackVisibility } from "./TrackVisibility";
import { VoiceDetection } from "./VoiceDetection";
export function Sidebar({ model }: { model: WorkspaceModel }) {
  const { } = model;
  return <><aside className="sidebar">
    <SavedProjects model={model} />
    <AnalysisSettings model={model} />
    <AnalysisStart model={model} />
    <VoiceDetection model={model} />
    <CancelJob model={model} />
    <TrackVisibility model={model} />
    <RuntimePanel model={model} />
  </aside></>;
}
