import { useState } from "react";
import type { Mode } from "../types";

export function useAnalysisSettings() {
  const [beatboxRecall, setBeatboxRecall] = useState(true);
  const [mode, setMode] = useState<Mode>("japanese");
  const [eventSensitivity, setEventSensitivity] = useState<"standard" | "sensitive">("standard");
  const [lyrics, setLyrics] = useState("");
  return { beatboxRecall, setBeatboxRecall, mode, setMode, eventSensitivity, setEventSensitivity, lyrics, setLyrics };
}
