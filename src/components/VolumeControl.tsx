import { useEffect, useState, type RefObject } from "react";

const STORAGE_KEY = "music-sweeper.playback-volume";
function readVolume() {
  try {
    const value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "null");
    if (value && typeof value.volume === "number" && Number.isFinite(value.volume)
      && value.volume >= 0 && value.volume <= 1) return value.muted === true ? 0 : value.volume as number;
  } catch { /* Playback remains available when browser storage is unavailable. */ }
  return 1;
}

export function VolumeControl({ audio, sourceKey }: { audio: RefObject<HTMLAudioElement | null>; sourceKey: string }) {
  const [volume, setVolume] = useState(readVolume);
  useEffect(() => {
    if (audio.current) { audio.current.volume = volume; audio.current.muted = false; }
  }, [audio, sourceKey, volume]);
  useEffect(() => {
    try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ volume })); }
    catch { /* A denied preference write must not interrupt playback. */ }
  }, [volume]);
  return <div className="volume-control">
    <label>音量<input aria-label="再生音量" type="range" min={0} max={100} step={1}
      value={Math.round(volume * 100)} onChange={e => setVolume(Number(e.target.value) / 100)} /></label>
    <output aria-live="off">{Math.round(volume * 100)}%</output>
  </div>;
}
