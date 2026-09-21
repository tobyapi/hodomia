vi.mock("./api", async () => (await import("./test/apiMock")).createApiMock());
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { App } from "./App";
import * as api from "./api";
import { fixture, openFixture } from "./test/appFixture";

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
  await openFixture();
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

test("chords can be refreshed without re-running lyrics or voice detection", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
  fireEvent.change(screen.getByLabelText("編集トラック"), { target: { value: "chords" } });
  fireEvent.click(screen.getByRole("button", { name: "コード・キーだけ再推定" }));
  await waitFor(() => expect(api.analyze).toHaveBeenCalledWith(fixture.root, expect.objectContaining({ scope: "harmony" })));
});
