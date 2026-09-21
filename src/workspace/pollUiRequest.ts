import type { Snapshot, UiRequest } from "../types";
import type { WorkspaceState } from "./useWorkspaceState";

function installInterval(state: WorkspaceState, install: (value: Snapshot) => void, request: UiRequest, value: Snapshot) {
  if (request.stem !== "original" && !value.result.stems?.[request.stem]) throw new Error("指定した分離音声がありません。");
  install(value); state.setTrack(request.track); state.setStem(request.stem);
  state.setLoop({ start: request.start, end: request.end });
  state.currentTime.current = request.start; state.setTime(request.start);
  if (state.audio.current && state.snapshot?.root === request.root && state.stem === request.stem) {
    state.audio.current.currentTime = request.start;
  }
  state.setMessage("AIが指定した区間を開きました。再生ボタンで試聴できます。");
}
export async function pollUiRequest(state: WorkspaceState, install: (value: Snapshot) => void, alive: () => boolean) {
  const request = await state.api.nextUiRequest();
  if (!alive() || !request) return;
  try {
    const value = await state.api.openProject(request.root);
    if (!alive()) return;
    installInterval(state, install, request, value);
    await state.api.ackUiRequest(request.requestId, "applied");
  } catch (error) {
    await state.api.ackUiRequest(request.requestId, "failed", String(error));
    if (alive()) state.setError(String(error));
  }
}
