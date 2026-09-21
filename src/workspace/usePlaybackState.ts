import { useRef, useState } from "react";

export function usePlaybackState() {
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [stem, setStem] = useState("original");
  const [loop, setLoop] = useState<{ start: number; end: number } | null>(null);
  const audio = useRef<HTMLAudioElement>(null);
  const currentTime = useRef(0);
  const switchingAudio = useRef(false);
  return { time, setTime, playing, setPlaying, stem, setStem, loop, setLoop, audio, currentTime, switchingAudio };
}
