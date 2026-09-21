import { timeLabel } from "../editing";
import type { WorkspaceModel } from "../workspace/useWorkspace";

export function RowsTable({ model }: { model: WorkspaceModel }) {
  const { selectedId, setSelectedId, rows, seek } = model;
  return <><div className="rows-table"><table><thead><tr><th>開始</th><th>終了</th><th>内容</th><th>確認</th></tr></thead><tbody>{rows.map(row => <tr key={row.id} className={selectedId === row.id ? "selected-row" : ""} onClick={() => { setSelectedId(row.id); if (row.start !== null) seek(row.start); }}><td>{row.start === null ? "未確定" : timeLabel(row.start)}</td><td>{row.end === null ? "—" : timeLabel(row.end)}</td><td><button className="row-select" onClick={() => setSelectedId(row.id)}>{row.label}{row.uncertain ? "（候補）" : ""}</button></td><td>{row.reviewed ? "確認済み" : "要確認"}</td></tr>)}</tbody></table>{!rows.length && <p className="empty-rows">このトラックにはまだ項目がありません。分析するか、手動で追加できます。</p>}</div></>;
}
