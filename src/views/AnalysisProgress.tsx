import type { WorkspaceModel } from "../workspace/useWorkspace";

export function AnalysisProgress({ model }: { model: WorkspaceModel }) {
  const { snapshot, job } = model;
  if (!snapshot) return null;
  return <><div className="analysis-progress"><span>{job.running && job.kind === "analysis" ? snapshot.status.stage : snapshot.status.state === "running" ? "前回の解析は中断されています。再分析できます。" : snapshot.status.stage}</span>
    <span>{snapshot.status.elapsed ? Math.round(snapshot.status.elapsed) + " 秒" : ""}</span><progress max={1} value={snapshot.status.progress ?? 0} /></div></>;
}
