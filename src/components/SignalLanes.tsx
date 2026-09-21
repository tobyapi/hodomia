import type { Analysis, Point, TimelineRow } from "../types";
import { STEM_NAMES } from "../types";
import { Curve } from "./Curve";
import type { LaneRenderer } from "./TrackLanes";

export function SignalLanes({ analysis, visible, lane, duration, width }: {
  analysis: Analysis; visible: Record<string, boolean>; lane: LaneRenderer; duration: number; width: number;
}) {
  return <>
    {visible.energy && lane("盛り上がり", <Curve points={analysis.series?.energy ?? []} duration={duration} width={width} color="var(--energy)" />, "energy")}
    {visible.pitch && lane("主旋律 / 音高", <Curve points={analysis.series?.pitch?.points ?? []} duration={duration} width={width} color="var(--pitch)" pitch />, "pitch")}
    {visible.stems && <StemLanes analysis={analysis} lane={lane} duration={duration} width={width} />}
  </>;
}
function StemLanes({ analysis, lane, duration, width }: {
  analysis: Analysis; lane: LaneRenderer; duration: number; width: number;
}) {
  return <>{Object.entries(STEM_NAMES).map(([name, label]) => {
    const data = analysis.series?.[name] as { levels?: Point[]; regions?: TimelineRow[] } | undefined;
    return lane(label, <><Curve points={data?.levels ?? []} duration={duration} width={width} color="var(--stem)" />
      {data?.regions?.map(row => <rect key={row.id} x={row.start! / duration * width} y={67}
        width={(row.end! - row.start!) / duration * width} height={5} fill="var(--stem)" />)}</>, name);
  })}</>;
}
