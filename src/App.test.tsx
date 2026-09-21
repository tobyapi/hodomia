vi.mock("./api", async () => (await import("./test/apiMock")).createApiMock());
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { App } from "./App";
import * as api from "./api";
import { fixture } from "./test/appFixture";

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

test("native failure is visible and can be retried", async () => {
  vi.mocked(api.openProject).mockRejectedValueOnce(new Error("破損したプロジェクト"));
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("破損したプロジェクト");
  expect(screen.getByRole("button", { name: "プロジェクトを開く" })).toBeEnabled();
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
