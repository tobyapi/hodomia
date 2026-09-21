import type { Snapshot } from "../types";
import type { WorkspaceState } from "./useWorkspaceState";

export function createProjectActions(state: WorkspaceState) {
  const { snapshot, setSnapshot, setSavedProjects, setMessage, setError, setExternalChange, setLyrics, setSelectedId, setViewAuto, editor, setTime, setPlaying, setStem, setLoop, audio, currentTime, api } = state;
  function install(value: Snapshot) {
    setExternalChange(false);
    audio.current?.pause(); setSnapshot(value); editor.reset(value.edits.tracks);
    setTime(0); currentTime.current = 0; setPlaying(false); setStem("original"); setLoop(null); setSelectedId(undefined);
    setViewAuto(false); setLyrics(""); setMessage("プロジェクトを開きました。");
    void api.savedProjects().then(setSavedProjects).catch(e => setError("保存した曲の一覧を更新できません: " + String(e)));
  }
  async function save() {
    if (!snapshot) return;
    const edits = await api.saveEdits(snapshot.root, { revision: snapshot.edits.revision, tracks: editor.tracks });
    setSnapshot(s => s ? { ...s, edits } : s); editor.markSaved(); setMessage("修正を保存しました。");
  }
  async function open(create: boolean) {
    if (editor.dirty) await save();
    if (create) {
      const source = await api.choose("source"); if (!source) return;
      setMessage("音源をコピーして読み込んでいます…");
      install(await api.createProject(source));
    } else {
      const root = await api.choose("project"); if (root) install(await api.openProject(root));
    }
  }
  return { install, save, open };
}
