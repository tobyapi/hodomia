vi.mock("./api", async () => (await import("./test/apiMock")).createApiMock());
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { App } from "./App";
import * as api from "./api";
import { fixture } from "./test/appFixture";

test("saved comparison metadata does not re-enable retired models or playback sources", async () => {
  const value = structuredClone(fixture);
  value.result.stems = { vocals: 'stems/vocals.wav' };
  Object.assign(value.result, { vocalComparisons: { variants: [] }, separationComparison: { stems: { melband_vocals: 'old.wav' } } });
  vi.mocked(api.openProject).mockResolvedValue(value);
  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: 'プロジェクトを開く' }));
  await screen.findByRole('heading', { name: 'テスト曲' });
  fireEvent.change(screen.getByLabelText('編集トラック'), { target: { value: 'vocalEvents' } });
  expect(screen.queryByRole('button', { name: /YAMNet|Mel-Band/ })).not.toBeInTheDocument();
  expect(screen.getByLabelText('試聴する音声').querySelectorAll('option')).toHaveLength(2);
  expect(screen.getByRole('button', { name: '声の表現だけ検出' })).toBeEnabled();
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
