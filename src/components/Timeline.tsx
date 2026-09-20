import { useRef } from "react";
import type { Analysis, Point, TimelineRow, Track, Tracks } from "../types";
import { TRACK_NAMES, STEM_NAMES, VOCAL_CATEGORIES } from "../types";
import { timeLabel } from "../editing";

type Props = { duration: number; time: number; zoom: number; tracks: Tracks; analysis: Analysis;
  visible: Record<string, boolean>; selected?: string; onSeek: (time: number) => void;
  onSelect: (track: Track, row: TimelineRow) => void };

function Curve({ points, duration, width, color, pitch = false }: { points: Point[]; duration: number; width: number; color: string; pitch?: boolean }) {
  const paths: string[] = [];
  let current = "";
  for (const p of points) {
    if (p.value === null) { if (current) paths.push(current); current = ""; continue; }
    const height = pitch ? Math.max(0, Math.min(1, (p.value - 36) / 60)) : Math.max(0, Math.min(1, p.value));
    current += (current ? " L" : "M") + (p.time / duration * width).toFixed(1) + " " + (66 - height * 54).toFixed(1);
  }
  if (current) paths.push(current);
  return <>{paths.map((d, i) => <path key={i} d={d} stroke={color} strokeWidth={1.5} fill="none" />)}</>;
}

export function Timeline({ duration, time, zoom, tracks, analysis, visible, selected, onSeek, onSelect }: Props) {
  const width = Math.max(700, duration * zoom);
  const scroll = useRef<HTMLDivElement>(null);
  const cursor = time / duration * width;
  const waveform = analysis.series?.waveform ?? [];
  const line = <line x1={cursor} x2={cursor} y1={0} y2={76} stroke="#fff" opacity={.85} />;
  const seek = (e: React.MouseEvent<SVGSVGElement>) => {
    const bounds = e.currentTarget.getBoundingClientRect();
    onSeek(Math.max(0, Math.min(duration, (e.clientX - bounds.left) / bounds.width * duration)));
  };
  function lane(label: string, content: React.ReactNode, key: string) {
    return <div className="lane" key={key}><div className="lane-label">{label}</div><svg width={width} height={76} onClick={seek} aria-label={label + " タイムライン"}>{content}{line}</svg></div>;
  }
  const ticks = Array.from({ length: Math.ceil(duration / (zoom > 15 ? 5 : 10)) }, (_, i) => i * (zoom > 15 ? 5 : 10));
  return <div className="timeline-scroll" ref={scroll}>
    <div className="timeline-inner" style={{ width: width + 112 }}>
      <div className="ruler"><div className="lane-label">MIN : SEC</div><svg width={width} height={32} onClick={seek}>{ticks.map(t => <g key={t}><line x1={t / duration * width} x2={t / duration * width} y1={22} y2={32} stroke="#536375" /><text x={t / duration * width + 5} y={16}>{timeLabel(t).slice(0, 5)}</text></g>)}</svg></div>
      {lane("波形", waveform.map((v, i) => <line key={i} x1={i / waveform.length * width} x2={i / waveform.length * width} y1={38 - v * 31} y2={38 + v * 31} stroke="#65cfb2" strokeWidth={Math.max(.6, width / waveform.length)} />), "wave")}
      {(Object.keys(TRACK_NAMES) as Track[]).filter(t => visible[t]).flatMap(track => {
        const groups: [string, TimelineRow[]][] = track === "vocalEvents"
          ? Object.entries(VOCAL_CATEGORIES).filter(([category]) => (tracks[track] ?? []).some(r => (r.category ?? "other") === category)).map(([category, name]) => [name, (tracks[track] ?? []).filter(r => (r.category ?? "other") === category)])
          : [[TRACK_NAMES[track], tracks[track] ?? []]];
        if (!groups.length) groups.push([TRACK_NAMES[track], []]);
        return groups.map(([name, rows], group) => lane(name, rows.filter(r => r.start !== null && r.end !== null).map(r => {
        const x = r.start! / duration * width, w = Math.max(track === "beats" ? 2 : 5, (r.end! - r.start!) / duration * width);
        return <g key={r.id} className={"region " + track + (selected === r.id ? " selected" : "")} onClick={e => { e.stopPropagation(); onSelect(track, r); onSeek(r.start!); }} role="button" tabIndex={0} aria-label={r.label + " " + timeLabel(r.start!)} onKeyDown={e => { if (e.key === "Enter") { onSelect(track, r); onSeek(r.start!); } }}>
          <title>{r.label} · {r.warning ?? ""}</title>
          <rect x={x} y={track === "beats" ? (r.label === "1" ? 8 : 27) : 15} width={w} height={track === "beats" ? (r.label === "1" ? 58 : 39) : 45} rx={track === "beats" ? 0 : 4} />
          {track !== "beats" && w > 22 && <text x={x + 7} y={43}>{r.label.slice(0, Math.max(1, Math.floor(w / 12) - 1))}</text>}
        </g>;
      }), track + group)); })}
      {visible.energy && lane("盛り上がり", <Curve points={analysis.series?.energy ?? []} duration={duration} width={width} color="#f9c977" />, "energy")}
      {visible.pitch && lane("主旋律 / 音高", <Curve points={analysis.series?.pitch?.points ?? []} duration={duration} width={width} color="#c9a5ff" pitch />, "pitch")}
      {visible.stems && Object.entries(STEM_NAMES).map(([name, label]) => {
        const data = analysis.series?.[name] as { levels?: Point[]; regions?: TimelineRow[] } | undefined;
        return lane(label, <><Curve points={data?.levels ?? []} duration={duration} width={width} color="#69a8eb" />{data?.regions?.map(r => <rect key={r.id} x={r.start! / duration * width} y={67} width={(r.end! - r.start!) / duration * width} height={5} fill="#69a8eb" />)}</>, name);
      })}
    </div>
  </div>;
}
