import type { TimelineRow } from "../types";
import { STEM_NAMES, VOCAL_CATEGORIES } from "../types";

export function EventEvidence({ row }: { row: TimelineRow }) {
  if (row.score === undefined) return null;
  return <div className="event-evidence"><p>元の推定：{VOCAL_CATEGORIES[row.detectedCategory ?? row.category ?? "other"]}</p>
    <p>モデルスコア {row.score.toFixed(3)}（正解率ではありません）</p>
    <p>参照音声：{row.evidenceSources?.map(s => s === "original" ? "原曲" : STEM_NAMES[s] ?? s).join("・")}</p>
    <p className="muted">「あー」「うー」やスキャットを含め、歌唱との区別が難しい声は手動で分類できます。</p></div>;
}
