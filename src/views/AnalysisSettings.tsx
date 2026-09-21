import type { WorkspaceModel } from "../workspace/useWorkspace";

import type { Mode } from "../types";

export function AnalysisSettings({ model }: { model: WorkspaceModel }) {
  const { guarded, mode, setMode, lyrics, setLyrics, locked, desktop, api } = model;
  return <><div className="eyebrow">ANALYSIS</div><h2>曲を分析する</h2>
    <label>解析モード<select value={mode} disabled={locked} onChange={e => setMode(e.target.value as Mode)}><option value="japanese">日本語歌唱・精度優先</option><option value="multilingual">多言語の歌もの</option><option value="instrumental">インストゥルメンタル</option></select></label>
    <p className="muted">{mode === "japanese" ? "分離した歌声を日本語に固定して認識し、歌詞の時刻を精密に合わせます。" : mode === "instrumental" ? "歌詞の認識を省き、音楽の構造と主旋律を分析します。" : "言語を自動判別します。歌詞と時刻は推定候補として表示します。"}</p>
    {mode !== "instrumental" && <><label>歌詞（任意）<textarea placeholder={"正しい歌詞があれば貼り付け\n1行＝1フレーズ、繰り返しも曲順に"} rows={6} value={lyrics} disabled={locked} onChange={e => setLyrics(e.target.value)} /></label>
      <button className="text-button" disabled={!desktop || locked} onClick={() => void guarded(async () => { const path = await api.choose("lyrics"); if (path) setLyrics(await api.readLyrics(path)); })}>テキストファイルから読み込む</button></>}</>;
}
