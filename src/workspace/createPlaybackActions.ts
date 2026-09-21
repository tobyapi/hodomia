import type { WorkspaceState } from "./useWorkspaceState";

export function createPlaybackActions(state: WorkspaceState) {
  const { setError, setTime, audio, currentTime, duration } = state;
  function seek(value: number) {
    const next = Math.min(duration, Math.max(0, value));
    if (audio.current) audio.current.currentTime = next;
    setTime(next); currentTime.current = next;
  }
  async function togglePlay() {
    if (!audio.current) return;
    if (audio.current.paused) { try { await audio.current.play(); } catch (e) { setError("再生できません: " + String(e)); } }
    else audio.current.pause();
  }
  return { seek, togglePlay };
}
