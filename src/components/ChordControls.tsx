import type { Analysis } from "../types";

export function ChordControls({ analysis, ready, locked, onAnalyze }: {
  analysis: Analysis; ready: boolean; locked: boolean; onAnalyze: () => void;
}) {
  const current = (analysis.engines?.chords as { backend?: string } | undefined)?.backend;
  const legacy = !!analysis.tracks?.chords?.length && current !== "chordmini-btc";
  return <div className="event-note chord-controls">
    <p className="muted">コード分析：BTC · 原曲を使用 · 平滑化なし。キーは従来の調性推定です。</p>
    {legacy && <p className="muted">表示中のコードは以前の方式で解析した結果です。再推定するとBTCの結果を保存します。手修正は保持します。</p>}
    <button disabled={locked || !ready} onClick={onAnalyze}>コード・キーだけ再推定</button>
    {!ready && <p className="muted">左の「コードモデルをセットアップ」でBTCを準備してください。</p>}
  </div>;
}
