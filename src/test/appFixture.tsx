import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";
import { App } from "../App";
import * as api from "../api";
import type { Snapshot } from "../types";
export const fixture: Snapshot = {
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
  vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => { });
});
export async function openFixture() {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "プロジェクトを開く" }));
  await screen.findByRole("heading", { name: "テスト曲" });
}
