import type * as NativeApi from "../api";
import { createAnalysisActions } from "./createAnalysisActions";
import { createEditingActions } from "./createEditingActions";
import { createPlaybackActions } from "./createPlaybackActions";
import { createProjectActions } from "./createProjectActions";
import { useWorkspaceEffects } from "./useWorkspaceEffects";
import { useWorkspacePolling } from "./useWorkspacePolling";
import { useWorkspaceState } from "./useWorkspaceState";

export function useWorkspace(api: typeof NativeApi) {
  const state = useWorkspaceState(api);
  const project = createProjectActions(state);
  const analysis = createAnalysisActions(state, project.save);
  const editing = createEditingActions(state);
  const playback = createPlaybackActions(state);
  useWorkspacePolling(state, project.install);
  useWorkspaceEffects(state, project.save);
  return { ...state, ...project, ...analysis, ...editing, ...playback };
}
export type WorkspaceModel = ReturnType<typeof useWorkspace>;
