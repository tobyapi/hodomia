import type { WorkspaceModel } from "../workspace/useWorkspace";

export function CancelJob({ model }: { model: WorkspaceModel }) {
  const { job, setMessage, guarded, api } = model;
  return <>{job.running && <button className="full danger" disabled={job.cancelRequested} onClick={() => void guarded(async () => { await api.cancelJob(job.jobId); setMessage("中止を要求しました。現在の処理の区切りまで待っています。"); })}>{job.cancelRequested ? "中止待ち…" : "処理を中止"}</button>}</>;
}
