export type Mode = "multilingual" | "japanese" | "instrumental";
export type SavedProject = { root: string; name: string; duration: number; createdAt: string | null; hasAnalysis: boolean };
export type Track = "beats" | "sections" | "lyrics" | "words" | "vocalEvents" | "chords" | "key";
export type VocalCategory = "beatbox" | "breath" | "humming" | "other" | "rap" | "spoken";
export type TimelineRow = {
  id: string; start: number | null; end: number | null; label: string;
  reviewed?: boolean; warning?: string; language?: string; parentId?: string; uncertain?: boolean;
  category?: VocalCategory; detectedCategory?: VocalCategory; score?: number; method?: string;
  evidenceSources?: string[]; evidenceLabels?: string[]; timingUncertainty?: number;
};
export type Tracks = Partial<Record<Track, TimelineRow[]>>;
export type Edits = { revision: number; tracks: Tracks };
export type Point = { time: number; value: number | null };
export type Analysis = {
  runId?: string; mode?: Mode; bpm?: number | null; tracks?: Tracks;
  stems?: Record<string, string>; engines?: Record<string, unknown>;
  series?: {
    waveform?: number[]; energy?: Point[]; tempo?: Point[];
    pitch?: { points: Point[]; warning: string };
    [key: string]: unknown;
  };
};
export type Snapshot = {
  root: string;
  project: { name: string; duration: number; audio: string; currentRun: string | null; source: { path: string; sha256: string } };
  edits: Edits; result: Analysis;
  status: { state: string; stage: string; progress?: number; elapsed?: number; errors: { stage: string; message: string }[] };
};
export type Job = { running: boolean; success?: boolean | null; kind: string | null; log: string; jobId?: string; root?: string; state?: string; error?: string; cancelRequested?: boolean };
export type UiRequest = { requestId: string; root: string; start: number; end: number; stem: string; track: Track; state: string };
export type RuntimeStatus = { path: string; ready: boolean; analysisSupported: boolean; chordMiniReady?: boolean; details?: { cudaAvailable: boolean; torch: string } };
export type AnalysisOptions = { mode: Mode; lyrics: string; scope?: "vocal-events" | "harmony"; beatboxRecall?: boolean; eventSensitivity?: "standard" | "sensitive"; region?: { start: number; end: number; language: "ja" | "en" } };
export const TRACK_NAMES: Record<Track, string> = { beats: "拍・小節", sections: "曲構成", lyrics: "歌詞", words: "単語", vocalEvents: "声の表現", chords: "コード", key: "キー" };
export const VOCAL_CATEGORIES: Record<VocalCategory, string> = { rap: "ラップ", spoken: "朗読・語り", beatbox: "ビートボックス", breath: "ブレス", humming: "ハミング", other: "その他の非言語発声" };
export const STEM_NAMES: Record<string, string> = { vocals: "ボーカル", drums: "ドラム", bass: "ベース", other: "その他" };
