import type { Snapshot } from "../types";
import type { WorkspaceState } from "./useWorkspaceState";

export async function pollProject(state: WorkspaceState, alive: () => boolean) {
  const { api, snapshot, busy, setSavedProjects } = state;
  if (!busy) {
    const projects = await api.savedProjects();
    if (!alive()) return;
    setSavedProjects(projects);
  }
  if (!snapshot || busy) return;
  const value = await api.openProject(snapshot.root);
  if (!alive()) return;
  applySnapshot(state, value);
}

function applySnapshot(state: WorkspaceState, value: Snapshot) {
  const { snapshot, editor, draftDirty, setExternalChange, setSnapshot } = state;
  if (!snapshot) return;
  if (value.edits.revision !== snapshot.edits.revision && (editor.dirty || draftDirty)) {
    setExternalChange(true);
  } else if (!draftDirty) {
    if (value.edits.revision !== snapshot.edits.revision) editor.reset(value.edits.tracks);
    setExternalChange(false);
    setSnapshot(value);
  }
}
