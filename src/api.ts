import { convertFileSrc, invoke, isTauri } from "@tauri-apps/api/core";
import type { AnalysisOptions, Edits, Job, RuntimeStatus, Snapshot } from "./types";

export const desktop = () => isTauri();
export function asset(root: string, path: string) {
  return convertFileSrc(root.replace(/[\\/]$/, "") + "/" + path);
}
export const choose = (kind: "source" | "folder" | "project" | "lyrics") => invoke<string | null>("choose_path", { kind });
export const runtimeStatus = () => invoke<RuntimeStatus>("runtime_status");
export const jobStatus = () => invoke<Job>("job_status");
export const setupRuntime = () => invoke<void>("setup_runtime");
export const cancelJob = () => invoke<void>("cancel_job");
export const readLyrics = (path: string) => invoke<string>("read_lyrics", { path });
export const analyze = (root: string, options: AnalysisOptions) => invoke<void>("start_analysis", { root, options });
const operation = <T,>(operation: string, args: object) => invoke<T>("workspace_operation", { operation, args });
export const createProject = (source: string) => operation<Snapshot>("create", { source });
export const openProject = (root: string) => operation<Snapshot>("snapshot", { root });
export const saveEdits = (root: string, edits: Edits) => operation<Edits>("save", { root, edits });
export const exportProject = (root: string) => operation<{ path: string; untimedLyrics: number }>("export", { root });
