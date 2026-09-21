// Development-only browser harness. Vite's production entry is index.html.
import ReactDOM from "react-dom/client";
import { App } from "../../src/App";
import * as api from "../../src/api";
import type { Snapshot } from "../../src/types";
import "../../src/styles.css";

const response = await fetch("/test-results/ui-snapshot.json");
if (!response.ok) throw new Error("Run npm run harness:prepare -- <project-folder> first");
const value: Snapshot = await response.json();
let hidden = false;
const bridge: typeof api = {
  ...api,
  nextUiRequest: async () => null,
  ackUiRequest: async () => { throw new Error("表示要求はありません。"); },
  desktop: () => true,
  savedProjects: async () => hidden ? [] : [{ root: value.root, name: value.project.name, duration: value.project.duration, createdAt: null, hasAnalysis: !!value.project.currentRun }],
  removeSavedProject: async () => { hidden = true; },
  deleteAnalysis: async () => { value.project.currentRun = null; value.result = {}; value.edits = { revision: value.edits.revision + 1, tracks: {} }; return structuredClone(value); },
  asset: (_root, path) => "/test-results/ui-media/" + (path === "audio.wav" ? "original.wav" : path.split("/").pop()),
  runtimeStatus: async () => ({ path: "UI検証用。保存はメモリー内のみ。", ready: true, chordMiniReady: true, yamnetReady: true, melbandReady: true }),
  jobStatus: async () => ({ running: false, kind: null, log: "ブラウザーUIハーネス。実際の分析はデスクトップで実行します。" }),
  choose: async () => value.root,
  openProject: async () => structuredClone(value),
  createProject: async () => structuredClone(value),
  saveEdits: async (_root, edits) => { value.edits = { ...edits, revision: edits.revision + 1 }; return value.edits; },
  exportProject: async () => ({ path: "UIハーネス：書き出しは実行しません", untimedLyrics: 0 }),
  analyze: async () => { throw new Error("UIハーネス：分析はデスクトップで実行してください。"); },
  setupRuntime: async () => { throw new Error("UIハーネス：セットアップは実行しません。"); },
  cancelJob: async () => {},
  readLyrics: async () => "",
};
ReactDOM.createRoot(document.getElementById("root")!).render(<App bridge={bridge} />);
