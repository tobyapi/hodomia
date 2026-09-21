import type { WorkspaceModel } from "../workspace/useWorkspace";

export function VoiceDetection({ model }: { model: WorkspaceModel }) {
  const { snapshot, runtime, guarded, beatboxRecall, setBeatboxRecall, eventSensitivity, setEventSensitivity, locked, start } = model;
  return <><div className="section-divider"><label>声の表現の検出感度<select value={eventSensitivity} disabled={locked} onChange={e => setEventSensitivity(e.target.value as "standard" | "sensitive")}><option value="standard">標準</option><option value="sensitive">候補を多めに拾う</option></select></label>
    <p className="muted">ラップ・朗読／語り・ビートボックス・ブレス・ハミングの候補を表示。歌詞は削除しません。</p>
    <p className="muted">ラップ・朗読／語りの検出は実験的です。候補が出なくても、その発声がないとは限りません。</p>
    <label className="check-label"><input type="checkbox" checked={beatboxRecall} disabled={locked} onChange={e => setBeatboxRecall(e.target.checked)} />ビートボックスの候補を広く拾う</label><p className="muted">分離ボーカルの打撃音も補助検出します。ラップ・ブレス・楽器漏れを含むため試聴して確認してください。</p>
    <button className="full" disabled={!snapshot || !runtime?.ready || locked} onClick={() => void guarded(() => start(undefined, "vocal-events"))}>声の表現だけ検出</button>
  </div></>;
}
