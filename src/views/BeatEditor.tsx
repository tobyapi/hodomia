import { beatGrid } from "../editing";
import type { WorkspaceModel } from "../workspace/useWorkspace";

export function BeatEditor({ model }: { model: WorkspaceModel }) {
  const { setError, track, bpm, setBpm, anchor, setAnchor, meter, setMeter, setViewAuto, editor, duration } = model;
  return <>{track === "beats" && <div className="beat-editor"><label>BPM<input aria-label="BPM" type="number" value={bpm} onChange={e => setBpm(e.target.value)} /></label><label>開始秒<input type="number" value={anchor} onChange={e => setAnchor(e.target.value)} /></label><label>小節の拍数<input type="number" value={meter} onChange={e => setMeter(e.target.value)} /></label><button onClick={() => { try { editor.change({ ...editor.tracks, beats: beatGrid(Number(bpm), Number(anchor), duration, Number(meter)) }); setViewAuto(false); } catch (e) { setError(String(e)); } }}>開始位置から拍を再配置</button></div>}</>;
}
