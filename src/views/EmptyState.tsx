import type { WorkspaceModel } from "../workspace/useWorkspace";
export function EmptyState({ model }: { model: WorkspaceModel }) {
  const { guarded, locked, desktop, runtime, open } = model;
  return <div className="empty-state"><div className="empty-wave">▂ ▄ ▆ ▃ █ ▅ ▂ ▇ ▄ ▆ ▂</div><div className="eyebrow">LISTEN DEEPER. CREATE BETTER.</div><h1>曲の展開を、ひとつの時間軸に。</h1><p>拍、歌詞、コード、楽器の出入り。<br />MVのアイデアにつながる音の変化を見つけましょう。</p><button className="primary" disabled={!desktop || locked || runtime?.analysisSupported === false} onClick={() => void guarded(() => open(true))}>最初の曲を読み込む</button><small>MP3 · MP4 · M4A · WAV · FLAC / 15分まで</small>{!desktop && <p className="muted">ファイルの分析はデスクトップアプリで利用できます。</p>}{runtime?.analysisSupported === false && <p className="muted">この環境では音源解析を利用できません。Windows x64 または Apple Silicon 搭載 Mac をご利用ください。</p>}</div>;
}
