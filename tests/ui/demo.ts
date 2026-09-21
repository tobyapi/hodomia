import type { Snapshot, TimelineRow } from "../../src/types";

const row = (id: string, start: number, end: number, label: string): TimelineRow =>
  ({ id, start, end, label, reviewed: false });

// Authored example data: no user audio, paths, lyrics or analysis results.
export const demo: Snapshot = {
  root: "demo",
  project: { name: "デモソング", duration: 64, audio: "audio.wav", currentRun: "demo-run", source: { path: "demo.wav", sha256: "" } },
  edits: { revision: 0, tracks: {} },
  status: { state: "complete", stage: "完了", progress: 100, errors: [] },
  result: {
    runId: "demo-run", mode: "japanese", bpm: 120,
    tracks: {
      beats: Array.from({ length: 128 }, (_, i) => row(`beat-${i}`, i / 2, i / 2 + 0.05, i % 4 === 0 ? "1" : String(i % 4 + 1))),
      sections: [row("s1", 0, 8, "イントロ"), row("s2", 8, 24, "Aメロ"), row("s3", 24, 32, "Bメロ"), row("s4", 32, 56, "サビ"), row("s5", 56, 64, "アウトロ")],
      lyrics: [row("l1", 8, 13, "朝の光が 窓をたたく"), row("l2", 16, 22, "新しい音を 探しに行こう"), row("l3", 24, 30, "遠くの空へ 手を伸ばして"), row("l4", 32, 39, "このメロディーに 想いを乗せて"), row("l5", 42, 49, "今日の景色を 歌にしよう"), row("l6", 50, 55, "もう一度 ここから")],
      chords: Array.from({ length: 16 }, (_, i) => row(`c${i}`, i * 4, i * 4 + 4, ["C", "G", "Am", "F"][i % 4])),
      key: [row("k1", 0, 64, "C major")],
      vocalEvents: [
        { ...row("v1", 1, 5, "ビートボックス"), category: "beatbox" },
        { ...row("v2", 14, 15, "ブレス"), category: "breath" },
        { ...row("v3", 57, 62, "ハミング"), category: "humming" },
      ],
    },
    series: {
      waveform: Array.from({ length: 640 }, (_, i) => 0.12 + Math.abs(Math.sin(i * 1.7) * Math.cos(i * 0.07)) * 0.7),
      energy: Array.from({ length: 128 }, (_, i) => ({ time: i / 2, value: 0.2 + 0.5 * Math.abs(Math.sin(i * 0.08)) })),
      pitch: { warning: "表示用の架空データ", points: Array.from({ length: 128 }, (_, i) => ({ time: i / 2, value: 60 + (i % 12) })) },
    },
  },
};
