import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { App } from "./App";
import * as api from "./api";
import type { Snapshot } from "./types";
vi.mock("./api", () => ({
  savedProjects: vi.fn(),
  nextUiRequest: vi.fn(), ackUiRequest: vi.fn(),
  removeSavedProject: vi.fn(), deleteAnalysis: vi.fn(),
  desktop: vi.fn(() => true), runtimeStatus: vi.fn(), jobStatus: vi.fn(), choose: vi.fn(),
  openProject: vi.fn(), createProject: vi.fn(), saveEdits: vi.fn(), exportProject: vi.fn(),
  analyze: vi.fn(), setupRuntime: vi.fn(), cancelJob: vi.fn(), readLyrics: vi.fn(),
  asset: vi.fn(() => "http://localhost/audio.wav"),
}));
const fixture: Snapshot = {
  root: "D:/test", project: { name: "テスト曲", duration: 60, audio: "audio.wav", currentRun: "run", source: { path: "source/test.wav", sha256: "hash" } },
  edits: { revision: 0, tracks: {} },
  result: { bpm: 120, tracks: { sections: [{ id: "s1", start: 10, end: 20, label: "サビ", reviewed: false }] }, stems: {} },
  status: { state: "complete", stage: "解析完了", progress: 1, errors: [] },
};
beforeEach(() => {
  vi.mocked(api.nextUiRequest).mockResolvedValue(null);
  vi.mocked(api.removeSavedProject).mockResolvedValue(undefined);
  vi.mocked(api.deleteAnalysis).mockResolvedValue(structuredClone(fixture));
  vi.mocked(api.savedProjects).mockResolvedValue([]);
  const preferences = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => preferences.get(key) ?? null,
    setItem: (key: string, value: string) => preferences.set(key, value),
  });
  vi.clearAllMocks(); vi.mocked(api.desktop).mockReturnValue(true);
  vi.mocked(api.runtimeStatus).mockResolvedValue({ path: "D:/runtime", ready: true, chordMiniReady: true });
  vi.mocked(api.jobStatus).mockResolvedValue({ running: false, kind: null, log: "" });
  vi.mocked(api.choose).mockResolvedValue("D:/test");
  vi.mocked(api.openProject).mockResolvedValue(structuredClone(fixture));
  vi.mocked(api.saveEdits).mockImplementation(async (_root, edits) => ({ ...edits, revision: edits.revision + 1 }));
  vi.mocked(api.analyze).mockResolvedValue({ jobId: "started-job" });
  vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
});
test("browser preview is explicit and cannot invoke native file selection", () => {
  vi.mocked(api.desktop).mockReturnValue(false);
  render(<App />);
  expect(screen.getByText("ブラウザープレビュー")).toBeVisible();
  expect(screen.getByRole("button", { name: "最初の曲を読み込む" })).toBeDisabled();
});

test("importing music opens only the source picker", async () => {
  vi.mocked(api.createProject).mockResolvedValue(structuredClone(fixture));
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "＋ 曲を読み込む" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  expect(api.choose).toHaveBeenCalledExactlyOnceWith("source");
  expect(api.createProject).toHaveBeenCalledExactlyOnceWith("D:/test");
});

test("cancelling the source picker does not open another dialog or create a project", async () => {
  vi.mocked(api.choose).mockResolvedValueOnce(null);
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "＋ 曲を読み込む" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "＋ 曲を読み込む" })).toBeEnabled());
  expect(api.choose).toHaveBeenCalledExactlyOnceWith("source");
  expect(api.createProject).not.toHaveBeenCalled();
});
test("loads project, edits section and persists without changing automatic results", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  expect(await screen.findByRole("heading", { name: "テスト曲" })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "サビ" }));
  fireEvent.change(screen.getByLabelText("内容"), { target: { value: "大サビ" } });
  fireEvent.click(screen.getByRole("button", { name: "変更を適用" }));
  fireEvent.click(screen.getByRole("button", { name: /修正を保存/ }));
  await waitFor(() => expect(api.saveEdits).toHaveBeenCalled());
  expect(vi.mocked(api.saveEdits).mock.calls[0][1].tracks.sections?.[0].label).toBe("大サビ");
  expect(fixture.result.tracks?.sections?.[0].label).toBe("サビ");
});
test("Japanese precision mode is sent to the backend", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.click(screen.getByRole("button", { name: "全体を再分析" }));
  await waitFor(() => expect(api.analyze).toHaveBeenCalledWith("D:/test", { mode: "japanese", lyrics: "", eventSensitivity: "standard", beatboxRecall: true }));
});

test("BTC is the only chord engine and old results and manual edits remain readable", async () => {
  const value = structuredClone(fixture);
  value.edits.tracks.chords = [{ id: "manual-chord", start: 0, end: 10, label: "手修正のコード" }];
  value.result.tracks!.chords = [{ id: "chord-0", start: 0, end: 10, label: "F:min7" }];
  value.result.engines = { chords: { backend: "chordmini-chordnet" } };
  vi.mocked(api.openProject).mockResolvedValue(value);
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.change(screen.getByLabelText("編集トラック"), { target: { value: "chords" } });
  expect(screen.getByRole("button", { name: "手修正のコード" })).toBeVisible();
  expect(screen.getByText(/表示中のコードは以前の方式/)).toBeVisible();
  expect(screen.queryByLabelText("コード推定方式")).not.toBeInTheDocument();
  expect(screen.queryByLabelText("保存したコード結果を比較")).not.toBeInTheDocument();
  fireEvent.click(screen.getByLabelText("自動結果を比較"));
  expect(screen.getByRole("button", { name: "F:min7" })).toBeVisible();
  fireEvent.click(screen.getByLabelText("自動結果を比較"));
  expect(screen.getByRole("button", { name: "手修正のコード" })).toBeVisible();
  expect(api.saveEdits).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "コード・キーだけ再推定" }));
  await waitFor(() => expect(api.analyze).toHaveBeenCalledWith(fixture.root, {
    mode: "japanese", lyrics: "", eventSensitivity: "standard", beatboxRecall: true, scope: "harmony",
  }));
});

test("missing BTC blocks chord and full analysis but allows setup and vocal analysis", async () => {
  vi.mocked(api.runtimeStatus).mockResolvedValue({ path: "D:/runtime", ready: true, chordMiniReady: false });
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.change(screen.getByLabelText("編集トラック"), { target: { value: "chords" } });
  expect(screen.getByRole("button", { name: "全体を再分析" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "コード・キーだけ再推定" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "声の表現だけ検出" })).toBeEnabled();
  fireEvent.click(screen.getByRole("button", { name: "コードモデルをセットアップ" }));
  await waitFor(() => expect(api.setupRuntime).toHaveBeenCalledExactlyOnceWith(true));
  expect(api.analyze).not.toHaveBeenCalled();
});

test("vocal-only analysis sends scope and sensitivity without requiring full reanalysis", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.change(screen.getByLabelText("声の表現の検出感度"), { target: { value: "sensitive" } });
  fireEvent.click(screen.getByRole("button", { name: "声の表現だけ検出" }));
  await waitFor(() => expect(api.analyze).toHaveBeenCalledWith("D:/test", {
    mode: "japanese", lyrics: "", scope: "vocal-events", eventSensitivity: "sensitive", beatboxRecall: true,
  }));
});

test("vocal candidates can be classified and saved without touching lyrics", async () => {
  const value = structuredClone(fixture);
  value.result.tracks!.lyrics = [{ id: "l1", start: 1, end: 3, label: "残す歌詞" }];
  value.result.tracks!.vocalEvents = [{ id: "v1", start: 0, end: 1, label: "ビートボックス", category: "beatbox", detectedCategory: "beatbox", score: .4 }];
  vi.mocked(api.openProject).mockResolvedValue(value);
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.change(screen.getByLabelText("編集トラック"), { target: { value: "vocalEvents" } });
  fireEvent.click(screen.getByRole("button", { name: "ビートボックス" }));
  expect(screen.getByText(/モデルスコア 0.400/)).toBeVisible();
  fireEvent.change(screen.getByLabelText("声の分類"), { target: { value: "humming" } });
  fireEvent.change(screen.getByLabelText("内容"), { target: { value: "んー" } });
  fireEvent.change(screen.getByLabelText("声の分類"), { target: { value: "other" } });
  fireEvent.click(screen.getByRole("button", { name: "変更を適用" }));
  fireEvent.click(screen.getByRole("button", { name: /修正を保存/ }));
  await waitFor(() => expect(api.saveEdits).toHaveBeenCalled());
  const edits = vi.mocked(api.saveEdits).mock.calls[0][1].tracks;
  expect(edits.vocalEvents?.[0].category).toBe("other");
  expect(edits.vocalEvents?.[0].label).toBe("んー");
  expect(edits.vocalEvents?.[0].detectedCategory).toBe("beatbox");
  expect(edits.lyrics).toBeUndefined();
  expect(value.result.tracks!.lyrics[0].label).toBe("残す歌詞");
});

test("changing stems keeps the seek position through media reload events", async () => {
  vi.mocked(api.openProject).mockResolvedValue({ ...structuredClone(fixture), result: { ...fixture.result, stems: { vocals: "vocals.wav" } } });
  const { container } = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.click(screen.getByRole("button", { name: "サビ" }));
  const audio = container.querySelector("audio")!;
  expect(audio.currentTime).toBe(10);
  fireEvent.change(screen.getByLabelText("試聴する音声"), { target: { value: "vocals" } });
  audio.currentTime = 0;
  fireEvent.timeUpdate(audio);
  fireEvent.loadedMetadata(audio);
  expect(audio.currentTime).toBe(10);
});
test("native failure is visible and can be retried", async () => {
  vi.mocked(api.openProject).mockRejectedValueOnce(new Error("破損したプロジェクト"));
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("破損したプロジェクト");
  expect(screen.getByRole("button", { name: "プロジェクトを開く" })).toBeEnabled();
});

test("playback volume survives stem changes and reopening the app", async () => {
  vi.mocked(api.openProject).mockResolvedValue({ ...structuredClone(fixture), result: { ...fixture.result, stems: { vocals: "vocals.wav" } } });
  const first = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  const audio = first.container.querySelector("audio")!;
  fireEvent.change(screen.getByLabelText("再生音量"), { target: { value: "35" } });
  expect(audio.volume).toBe(.35);
  fireEvent.change(screen.getByLabelText("試聴する音声"), { target: { value: "vocals" } });
  expect(audio.volume).toBe(.35);
  first.unmount();
  const second = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  const reopened = second.container.querySelector("audio")!;
  await waitFor(() => expect(reopened.volume).toBe(.35));
  expect(reopened.muted).toBe(false);
  expect(reopened.volume).toBe(.35);
  fireEvent.change(screen.getByLabelText("再生音量"), { target: { value: "0" } });
  expect(reopened.volume).toBe(0);
});

test("invalid saved volume falls back to a valid playback level", async () => {
  window.localStorage.setItem("music-sweeper.playback-volume", '{"volume":12,"muted":false}');
  const { container } = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  expect(container.querySelector("audio")!.volume).toBe(1);
});

test("player seek and ten-second controls keep playback inside the song", async () => {
  const { container } = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("region", { name: "音楽プレイヤー" });
  const audio = container.querySelector("audio")!;
  fireEvent.change(screen.getByLabelText("再生位置"), { target: { value: "56" } });
  expect(audio.currentTime).toBe(56);
  fireEvent.click(screen.getByRole("button", { name: "10秒進む" }));
  expect(audio.currentTime).toBe(60);
  fireEvent.click(screen.getByRole("button", { name: "10秒戻る" }));
  expect(audio.currentTime).toBe(50);
  fireEvent.click(screen.getByRole("button", { name: "先頭に戻る" }));
  fireEvent.click(screen.getByRole("button", { name: "10秒戻る" }));
  expect(audio.currentTime).toBe(0);
  fireEvent.click(screen.getByRole("button", { name: "ループ" }));
  expect(screen.getByRole("button", { name: "ループ" })).toHaveAttribute("aria-pressed", "true");
});

test("new delivery candidates can join manual edits without losing corrections or colliding IDs", async () => {
  const value = structuredClone(fixture);
  value.edits.tracks.vocalEvents = [{ id: "v1", start: 0, end: 1, label: "ブッ", category: "beatbox", reviewed: true }];
  value.result.tracks!.vocalEvents = [
    { id: "v1", start: 1, end: 5, label: "ラップ", category: "rap", reviewed: false },
    { id: "v2", start: 3, end: 6, label: "朗読・語り", category: "spoken", reviewed: false },
    { id: "v3", start: 0, end: 1, label: "その他の非言語発声", category: "other", reviewed: false },
    { id: "v4", start: 8, end: 9, label: "ビートボックス候補", category: "beatbox", method: "vocal-percussion", reviewed: false },
  ];
  vi.mocked(api.openProject).mockResolvedValue(value);
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.change(screen.getByLabelText("編集トラック"), { target: { value: "vocalEvents" } });
  fireEvent.click(screen.getByRole("button", { name: "未追加の声の分類を取り込む" }));
  expect(screen.getByLabelText("ラップ タイムライン")).toBeInTheDocument();
  expect(screen.getByLabelText("朗読・語り タイムライン")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "未追加の声の分類を取り込む" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /修正を保存/ }));
  await waitFor(() => expect(api.saveEdits).toHaveBeenCalled());
  const rows = vi.mocked(api.saveEdits).mock.calls[0][1].tracks.vocalEvents!;
  expect(rows[0]).toEqual(value.edits.tracks.vocalEvents[0]);
  expect(new Set(rows.map(r => r.id)).size).toBe(4);
  expect(rows.slice(1).every(r => !r.reviewed)).toBe(true);
});

test("saved songs reopen existing analysis without importing or reanalyzing", async () => {
  vi.mocked(api.savedProjects).mockResolvedValue([{ root: fixture.root, name: fixture.project.name, duration: 60, createdAt: null, hasAnalysis: true }]);
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "テスト曲を開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  expect(api.openProject).toHaveBeenCalledWith(fixture.root);
  expect(api.choose).not.toHaveBeenCalled();
  expect(api.createProject).not.toHaveBeenCalled();
  expect(api.analyze).not.toHaveBeenCalled();
});

test("removing a saved song requires confirmation and clears analysis before hiding it", async () => {
  vi.mocked(api.savedProjects).mockResolvedValue([{ root: fixture.root, name: fixture.project.name, duration: 60, createdAt: null, hasAnalysis: true }]);
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "テスト曲を削除" }));
  expect(api.deleteAnalysis).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "キャンセル" }));
  expect(api.deleteAnalysis).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "テスト曲を削除" }));
  vi.mocked(api.savedProjects).mockResolvedValue([]);
  fireEvent.click(screen.getByRole("button", { name: "解析データを削除" }));
  await waitFor(() => expect(api.removeSavedProject).toHaveBeenCalledWith(fixture.root));
  expect(api.deleteAnalysis).toHaveBeenCalledWith(fixture.root);
  expect(screen.queryByRole("button", { name: "テスト曲を開く" })).toBeNull();
});

test("chords can be refreshed without re-running lyrics or voice detection", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.change(screen.getByLabelText("編集トラック"), { target: { value: "chords" } });
  fireEvent.click(screen.getByRole("button", { name: "コード・キーだけ再推定" }));
  await waitFor(() => expect(api.analyze).toHaveBeenCalledWith(fixture.root, expect.objectContaining({ scope: "harmony" })));
});

test("external edits refresh a clean workspace", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  const changed = structuredClone(fixture);
  changed.edits = { revision: 1, tracks: { sections: [{ id: "s1", start: 10, end: 20, label: "AIの修正" }] } };
  vi.mocked(api.openProject).mockResolvedValue(changed);
  expect(await screen.findByRole("button", { name: "AIの修正" }, { timeout: 4000 })).toBeVisible();
  expect(api.saveEdits).not.toHaveBeenCalled();
});

test("external edits preserve unsaved changes and the old CAS revision", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.click(screen.getByRole("button", { name: "サビ" }));
  fireEvent.change(screen.getByLabelText("内容"), { target: { value: "手元の修正" } });
  fireEvent.click(screen.getByRole("button", { name: "変更を適用" }));
  const changed = structuredClone(fixture); changed.edits.revision = 1;
  vi.mocked(api.openProject).mockResolvedValue(changed);
  await screen.findByRole("button", { name: "最新の保存内容を読み込む" }, { timeout: 4000 });
  expect(screen.getByLabelText("内容")).toHaveValue("手元の修正");
  fireEvent.click(screen.getByRole("button", { name: /修正を保存/ }));
  await waitFor(() => expect(api.saveEdits).toHaveBeenCalledWith(fixture.root, expect.objectContaining({ revision: 0 })));
});

test("external edits preserve an inspector draft before apply", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.click(screen.getByRole("button", { name: "サビ" }));
  fireEvent.change(screen.getByLabelText("内容"), { target: { value: "入力中" } });
  const changed = structuredClone(fixture); changed.edits.revision = 2;
  vi.mocked(api.openProject).mockResolvedValue(changed);
  await screen.findByRole("button", { name: "最新の保存内容を読み込む" }, { timeout: 4000 });
  expect(screen.getByLabelText("内容")).toHaveValue("入力中");
});

test("queued display opens the requested track and time without autoplay", async () => {
  const request = { requestId: "display", root: fixture.root, start: 12, end: 18, track: "chords" as const, stem: "original", state: "queued" };
  vi.mocked(api.nextUiRequest).mockResolvedValueOnce(request);
  vi.mocked(api.ackUiRequest).mockResolvedValue({ ...request, state: "applied" });
  const { container } = render(<App />);
  await waitFor(() => expect(api.ackUiRequest).toHaveBeenCalledWith("display", "applied"));
  expect(screen.getByLabelText("編集トラック")).toHaveValue("chords");
  fireEvent.loadedMetadata(container.querySelector("audio")!);
  expect(container.querySelector("audio")?.currentTime).toBe(12);
  expect(container.querySelector("audio")?.paused).toBe(true);
});

test("cancel uses the job ID returned at start, before a subsequent status poll", async () => {
  vi.mocked(api.analyze).mockImplementation(async () => {
    vi.mocked(api.jobStatus).mockResolvedValue({ running: true, kind: "analysis", log: "", jobId: "started-job" });
    return { jobId: "started-job" };
  });
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.click(screen.getByRole("button", { name: "全体を再分析" }));
  fireEvent.click(await screen.findByRole("button", { name: "処理を中止" }));
  await waitFor(() => expect(api.cancelJob).toHaveBeenCalledWith("started-job"));
});
