vi.mock("./api", async () => (await import("./test/apiMock")).createApiMock());
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { App } from "./App";
import * as api from "./api";
import { fixture } from "./test/appFixture";

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
