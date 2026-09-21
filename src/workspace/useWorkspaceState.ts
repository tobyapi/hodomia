import type * as NativeApi from "../api";
import { useAnalysisSettings } from "./useAnalysisSettings";
import { usePlaybackState } from "./usePlaybackState";
import { useProjectState } from "./useProjectState";
import { useTimelineState } from "./useTimelineState";
import { workspaceSelection } from "./workspaceSelection";

export function useWorkspaceState(api: typeof NativeApi) {
  const project = useProjectState();
  const analysis = useAnalysisSettings();
  const timeline = useTimelineState();
  const playback = usePlaybackState();
  const state = { ...project, ...analysis, ...timeline, ...playback };
  return { ...state, ...workspaceSelection(state), api, desktop: api.desktop(), locked: project.busy || project.job.running };
}
export type WorkspaceState = ReturnType<typeof useWorkspaceState>;
