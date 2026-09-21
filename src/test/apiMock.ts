import { vi } from "vitest";
export function createApiMock() {
  return {
    savedProjects: vi.fn(),
    nextUiRequest: vi.fn(), ackUiRequest: vi.fn(),
    removeSavedProject: vi.fn(), deleteAnalysis: vi.fn(),
    desktop: vi.fn(() => true), runtimeStatus: vi.fn(), jobStatus: vi.fn(), choose: vi.fn(),
    openProject: vi.fn(), createProject: vi.fn(), saveEdits: vi.fn(), exportProject: vi.fn(),
    analyze: vi.fn(), setupRuntime: vi.fn(), cancelJob: vi.fn(), readLyrics: vi.fn(),
    asset: vi.fn(() => "http://localhost/audio.wav"),
  };
}
