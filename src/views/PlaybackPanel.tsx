import type { WorkspaceModel } from "../workspace/useWorkspace";

import { Player } from "../components/Player";

export function PlaybackPanel({ model }: { model: WorkspaceModel }) {
  const { snapshot, setError, zoom, setZoom, time, setTime, playing, setPlaying, stem, setStem, loop, setLoop, audio, currentTime, switchingAudio, duration, source, api, seek, togglePlay } = model;
  if (!snapshot) return null;
  return <><Player playing={playing} time={time} duration={duration} stem={stem}
    stems={Object.keys(snapshot.result.stems ?? {})} looping={!!loop} zoom={zoom} audio={audio} sourceKey={snapshot.root + "/" + source}
    onPlay={() => void togglePlay()} onSeek={seek} onStem={value => { switchingAudio.current = true; audio.current?.pause(); setStem(value); }}
    onLoop={() => setLoop(loop ? null : { start: 0, end: duration })} onZoom={setZoom} />
    <audio ref={audio} src={source ? api.asset(snapshot.root, source) : undefined} onLoadedMetadata={() => { if (audio.current) audio.current.currentTime = currentTime.current; switchingAudio.current = false; }} onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onEnded={() => setPlaying(false)} onTimeUpdate={() => {
      if (!audio.current || switchingAudio.current) return; const t = audio.current.currentTime;
      if (loop && (t >= loop.end || t < loop.start)) { audio.current.currentTime = loop.start; return; }
      currentTime.current = t; setTime(t);
    }} onError={() => setError("音声を再生できません。プロジェクト内の音声ファイルを確認してください。")} /></>;
}
