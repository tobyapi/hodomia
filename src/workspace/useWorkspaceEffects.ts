import { useEffect } from "react";
import * as nativeApi from "../api";
import { useCloseSave } from "../useCloseSave";
import type { WorkspaceState } from "./useWorkspaceState";

export function useWorkspaceEffects(state: WorkspaceState, save: () => Promise<void>) {
  const { snapshot, editor, setBpm, setError } = state;
  useEffect(() => {
    if (nativeApi.desktop()) return;
    const handler = (event: BeforeUnloadEvent) => { if (editor.dirty) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [editor.dirty]);
  useEffect(() => {
    if (snapshot?.result.bpm) setBpm(snapshot.result.bpm.toFixed(2));
  }, [snapshot?.result.bpm]);
  useCloseSave(editor.dirty, save, setError);
}
