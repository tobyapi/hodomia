import { useCallback, useState } from "react";
import type { Tracks } from "./types";

export function useEdits() {
  const [history, setHistory] = useState<Tracks[]>([{}]);
  const [index, setIndex] = useState(0);
  const [saved, setSaved] = useState("{}");
  const reset = useCallback((tracks: Tracks) => {
    setHistory([tracks]); setIndex(0); setSaved(JSON.stringify(tracks));
  }, []);
  const change = (tracks: Tracks) => { setHistory([...history.slice(0, index + 1), tracks]); setIndex(index + 1); };
  const tracks = history[index];
  return { tracks, reset, change, dirty: JSON.stringify(tracks) !== saved,
    markSaved: () => setSaved(JSON.stringify(tracks)),
    undo: () => setIndex(i => Math.max(0, i - 1)), redo: () => setIndex(i => Math.min(history.length - 1, i + 1)),
    canUndo: index > 0, canRedo: index < history.length - 1 };
}
