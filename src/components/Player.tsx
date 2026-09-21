import type { RefObject } from "react";
import { timeLabel } from "../editing";
import { STEM_NAMES } from "../types";
import { PlayerIcon } from "./PlayerIcon";
import { VolumeControl } from "./VolumeControl";

export function Player({ playing, time, duration, stem, stems, looping, zoom, audio, sourceKey,
  onPlay, onSeek, onStem, onLoop, onZoom }: {
  playing: boolean; time: number; duration: number; stem: string; stems: string[];
  looping: boolean; zoom: number; audio: RefObject<HTMLAudioElement | null>; sourceKey: string;
  onPlay: () => void; onSeek: (time: number) => void; onStem: (stem: string) => void;
  onLoop: () => void; onZoom: (zoom: number) => void;
}) {
  const progress = Math.max(0, Math.min(100, time / duration * 100));
  return <section className="music-player" aria-label="音楽プレイヤー">
    <div className="player-top">
      <div className="player-buttons">
        <button className="icon-button" aria-label="10秒戻る" title="10秒戻る" onClick={() => onSeek(Math.max(0, time - 10))}><PlayerIcon name="back10" /></button>
        <button className="player-play" aria-label={playing ? "一時停止" : "再生"} onClick={onPlay}><PlayerIcon name={playing ? "pause" : "play"} /></button>
        <button className="icon-button" aria-label="10秒進む" title="10秒進む" onClick={() => onSeek(Math.min(duration, time + 10))}><PlayerIcon name="forward10" /></button>
      </div>
    <div className="player-progress"><time>{timeLabel(time)}</time><input type="range" className="player-seek" aria-label="再生位置" aria-valuetext={`${timeLabel(time)} / ${timeLabel(duration)}`} min={0} max={duration} step={.01} value={time} onChange={e => onSeek(Number(e.target.value))} style={{ background: `linear-gradient(to right, var(--accent) ${progress}%, #35404e ${progress}%)` }} /><time>{timeLabel(duration)}</time></div>
      <div className="player-secondary"><button className="icon-button" aria-label="先頭に戻る" title="先頭に戻る" onClick={() => onSeek(0)}><PlayerIcon name="start" /></button><button className={"icon-button " + (looping ? "active" : "")} aria-label="ループ" title="ループ" aria-pressed={looping} onClick={onLoop}><PlayerIcon name="repeat" /></button></div>
    </div>
    <div className="player-bottom"><select aria-label="試聴する音声" value={stem} onChange={e => onStem(e.target.value)}><option value="original">オリジナル</option>{stems.map(s => <option key={s} value={s}>{STEM_NAMES[s] ?? s}</option>)}</select><VolumeControl audio={audio} sourceKey={sourceKey} /><label className="zoom-control">時間軸 <input aria-label="時間軸のズーム" type="range" min={2} max={40} value={zoom} onChange={e => onZoom(Number(e.target.value))} /></label></div>
  </section>;
}
