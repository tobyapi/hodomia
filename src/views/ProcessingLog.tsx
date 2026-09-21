import type { WorkspaceModel } from "../workspace/useWorkspace";

export function ProcessingLog({ model }: { model: WorkspaceModel }) {
  const { runtime, job, showLog } = model;
  return <>{showLog && <section className="log-panel"><h3>処理ログ</h3><p className="muted">{runtime?.path}</p><pre>{job.log || "まだログはありません。"}</pre></section>}</>;
}
