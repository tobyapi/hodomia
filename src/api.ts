import { convertFileSrc, invoke, isTauri } from "@tauri-apps/api/core";
import type { AnalysisOptions, Edits, Job, RuntimeStatus, Snapshot, SavedProject } from "./types";

export const desktop = () => isTauri();
export const savedProjects = () => invoke<SavedProject[]>("saved_projects");
export const removeSavedProject = (root: string) => invoke<void>("remove_saved_project", { root });
export function asset(root: string, path: string) {
  const joined = root.replace(/[\\/]$/, "") + "/" + path;
  // Windows verbatim paths (\\?\...) reject forward slashes, even in a suffix.
  const windows = /^[a-z]:[\\/]|^(\\\\|\/\/)/i.test(root);
  return convertFileSrc(windows ? joined.replace(/\//g, "\\") : joined);
}
export const choose = (kind: "source" | "folder" | "project" | "lyrics") => invoke<string | null>("choose_path", { kind });
export const runtimeStatus = () => invoke<RuntimeStatus>("runtime_status");
export const jobStatus = () => invoke<Job>("job_status");
export const setupRuntime = (chordMini = false) => invoke<void>("setup_runtime", { chordMini });
export const cancelJob = () => invoke<void>("cancel_job");
export const readLyrics = (path: string) => invoke<string>("read_lyrics", { path });
export const analyze = (root: string, options: AnalysisOptions) => invoke<void>("start_analysis", { root, options });
const operation = <T,>(operation: string, args: object) => invoke<T>("workspace_operation", { operation, args });
export const createProject = (source: string) => operation<Snapshot>("create", { source });
export const openProject = (root: string) => operation<Snapshot>("snapshot", { root });
export const saveEdits = (root: string, edits: Edits) => operation<Edits>("save", { root, edits });
export const exportProject = (root: string) => operation<{ path: string; untimedLyrics: number }>("export", { root });
export const deleteAnalysis = (root: string) => operation<Snapshot>("delete_analysis", { root });
