import { useEffect, useState, type RefObject } from "react";

const STORAGE_KEY = "music-sweeper.playback-volume";
const DEFAULT = { volume: 1, muted: false };

function readPreference() {
  try {
    const value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "null");
    if (value && typeof value.volume === "number" && Number.isFinite(value.volume)
      && value.volume >= 0 && value.volume <= 1 && typeof value.muted === "boolean") return value as typeof DEFAULT;
  } catch { /* Playback remains available when browser storage is unavailable. */ }
  return DEFAULT;
}

export function VolumeControl({ audio, sourceKey }: { audio: RefObject<HTMLAudioElement | null>; sourceKey: string }) {
  const [preference, setPreference] = useState(readPreference);
  const { volume, muted } = preference;
  useEffect(() => {
    if (audio.current) {
      audio.current.volume = volume;
      audio.current.muted = muted;
    }
  }, [audio, sourceKey, volume, muted]);
  useEffect(() => {
    try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preference)); }
    catch { /* A denied preference write must not interrupt playback. */ }
  }, [preference]);
  return <div className="volume-control">
    <button aria-label={muted ? "ミュート解除" : "ミュート"} aria-pressed={muted}
      onClick={() => setPreference({ volume, muted: !muted })}>{muted ? "消音中" : "消音"}</button>
    <label>音量 <input aria-label="再生音量" type="range" min={0} max={100} step={1}
      value={Math.round(volume * 100)} onChange={e => setPreference({ volume: Number(e.target.value) / 100, muted: false })} /></label>
    <output aria-live="off">{Math.round(volume * 100)}%</output>
  </div>;
}
