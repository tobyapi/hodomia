import { useRef } from "react";
import { timeLabel } from "../editing";
import type { Analysis, TimelineRow, Track, Tracks } from "../types";
import { SignalLanes } from "./SignalLanes";
import { TrackLanes } from "./TrackLanes";

type Props = {
  duration: number; time: number; zoom: number; tracks: Tracks; analysis: Analysis;
  visible: Record<string, boolean>; selected?: string; onSeek: (time: number) => void;
  onSelect: (track: Track, row: TimelineRow) => void
};

export function Timeline({ duration, time, zoom, tracks, analysis, visible, selected, onSeek, onSelect }: Props) {
  const width = Math.max(700, duration * zoom);
  const scroll = useRef<HTMLDivElement>(null);
  const cursor = time / duration * width;
  const waveform = analysis.series?.waveform ?? [];
  const line = <line x1={cursor} x2={cursor} y1={0} y2={76} stroke="var(--playhead)" opacity={.85} />;
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
      <div className="ruler"><div className="lane-label">MIN : SEC</div><svg width={width} height={32} onClick={seek}>{ticks.map(t => <g key={t}><line x1={t / duration * width} x2={t / duration * width} y1={22} y2={32} stroke="var(--line)" /><text x={t / duration * width + 5} y={16}>{timeLabel(t).slice(0, 5)}</text></g>)}</svg></div>
      {lane("波形", waveform.map((v, i) => <line key={i} x1={i / waveform.length * width} x2={i / waveform.length * width} y1={38 - v * 31} y2={38 + v * 31} stroke="var(--waveform)" strokeWidth={Math.max(.6, width / waveform.length)} />), "wave")}
      <TrackLanes tracks={tracks} visible={visible} lane={lane} duration={duration} width={width} selected={selected} onSelect={onSelect} onSeek={onSeek} />
      <SignalLanes analysis={analysis} visible={visible} lane={lane} duration={duration} width={width} />
    </div>
  </div>;
}
