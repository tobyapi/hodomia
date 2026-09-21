import type { WorkspaceModel } from "../workspace/useWorkspace";

export function AnalysisErrors({ model }: { model: WorkspaceModel }) {
  const { snapshot } = model;
  if (!snapshot) return null;
  return <>{!!snapshot.status.errors.length && <section className="analysis-errors"><h3>確認が必要な解析</h3>{snapshot.status.errors.map((e, i) => <p key={i}><strong>{e.stage}</strong> — {e.message}</p>)}</section>}</>;
}
