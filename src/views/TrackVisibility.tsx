import type { WorkspaceModel } from "../workspace/useWorkspace";

import { TRACK_NAMES } from "../types";

export function TrackVisibility({ model }: { model: WorkspaceModel }) {
  const { visible, setVisible } = model;
  return <><div className="section-divider"><div className="eyebrow">TRACKS</div>
    {Object.entries({ ...TRACK_NAMES, energy: "盛り上がり", pitch: "主旋律", stems: "楽器の出入り" }).map(([id, name]) => <label className="track-toggle" key={id}><input type="checkbox" checked={visible[id]} onChange={e => setVisible({ ...visible, [id]: e.target.checked })} />{name}</label>)}
  </div></>;
}
