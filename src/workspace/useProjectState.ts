import { useCallback, useRef, useState } from "react";
import type { Job, RuntimeStatus, SavedProject, Snapshot } from "../types";

export function useProjectState() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [savedProjects, setSavedProjects] = useState<SavedProject[]>([]);
  const [deleteTarget, setDeleteTarget] = useState<SavedProject | null>(null);
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);
  const [job, setJob] = useState<Job>({ running: false, kind: null, log: "" });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [showLog, setShowLog] = useState(false);
  const [externalChange, setExternalChange] = useState(false);
  const previousRunning = useRef(false);
  const guarded = useCallback(async (action: () => Promise<void>) => {
    setError(""); setBusy(true);
    try { await action(); } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }, []);
  return { snapshot, setSnapshot, savedProjects, setSavedProjects, deleteTarget, setDeleteTarget, runtime, setRuntime, job, setJob, busy, setBusy, message, setMessage, error, setError, showLog, setShowLog, externalChange, setExternalChange, previousRunning, guarded };
}
