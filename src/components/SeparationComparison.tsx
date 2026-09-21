import type { Analysis } from "../types";

export function SeparationComparison({ data, hasDemucs, ready, yamnetReady, locked, source, onSetup, onAnalyze, onSource }: {
  data?: Analysis["separationComparison"]; hasDemucs: boolean; ready: boolean; yamnetReady: boolean;
  locked: boolean; source: string; onSetup: () => void; onAnalyze: () => void; onSource: (source: string) => void;
}) {
  return <section className="vocal-comparison" aria-label="ボーカル分離の比較">
    <div className="comparison-heading"><strong>ボーカル分離を比較</strong><div className="button-row">
      {ready ? <button disabled={locked || !yamnetReady} onClick={onAnalyze}>Mel-Bandで分離して比較</button>
        : <button disabled={locked} onClick={onSetup}>Mel-Bandをセットアップ</button>}
    </div></div>
    <p className="muted">原曲からMel-Bandのボーカルと伴奏を作り、AST / YAMNetの検出を比較します。歌詞・通常の声の表現・手修正は保持します。</p>
    {ready && !yamnetReady && <p className="muted">下の「YAMNetをセットアップ」を先に実行してください。</p>}
    <div className="button-row" aria-label="同じ位置で音声を切り替え">
      <button aria-pressed={source === "original"} onClick={() => onSource("original")}>原曲</button>
      <button disabled={!hasDemucs} aria-pressed={source === "vocals"} onClick={() => onSource("vocals")}>Demucs ボーカル</button>
      <button disabled={!data?.stems.melband_vocals} aria-pressed={source === "melband_vocals"} onClick={() => onSource("melband_vocals")}>Mel-Band ボーカル</button>
      <button disabled={!data?.stems.melband_instrumental} aria-pressed={source === "melband_instrumental"} onClick={() => onSource("melband_instrumental")}>Mel-Band 伴奏</button>
    </div>
    <p className="muted">再生位置とループ区間を保って切り替えます。再生ボタンで、息や口の打撃音がどちら側に残っているか確認してください。</p>
    {data && <p className="muted">保存済み · Kimberley Jensen版 · 処理窓 {(data.engine.settings.segmentSize - 1) / 100}秒 · {data.engine.device}{data.engine.fallback ? "（GPUメモリー不足のため短い窓で実行）" : ""}。ノイズ除去・ゲートは追加していません。</p>}
  </section>;
}
