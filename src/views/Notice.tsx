import type { WorkspaceModel } from "../workspace/useWorkspace";

export function Notice({ model }: { model: WorkspaceModel }) {
  const { message, setMessage, error, setError } = model;
  return <>{(error || message) && <div className={"notice " + (error ? "error-notice" : "")} role={error ? "alert" : "status"}><span>{error || message}</span><button aria-label="通知を閉じる" onClick={() => { setError(""); setMessage(""); }}>×</button></div>}</>;
}
