import { useState } from "react";
import type { ComparisonCategory, VocalComparison as Comparison, VocalVariant } from "../types";
import { VOCAL_CATEGORIES, STEM_NAMES } from "../types";
import { timeLabel } from "../editing";

const names = (variant: VocalVariant) => `${variant.model.toUpperCase()} · ${variant.source === "original" ? "原曲" : STEM_NAMES[variant.source] ?? variant.source}`;

export function VocalComparison({ data, duration, time, zoom, ready, locked, onAnalyze, onSetup, onAudition }: {
  data?: Comparison; duration: number; time: number; zoom: number; ready: boolean; locked: boolean;
  onAnalyze: () => void; onSetup: () => void;
  onAudition: (source: string, start: number, end: number) => void;
}) {
  const [category, setCategory] = useState<ComparisonCategory>("beatbox");
  const [selectedVariant, setSelectedVariant] = useState("");
  const variants = data?.variants ?? [];
  const selected = variants.find(v => v.id === selectedVariant) ?? variants[0];
  const width = Math.max(700, duration * zoom);
  const candidates = selected?.candidates.filter(r => r.category === category) ?? [];
  return <section className="vocal-comparison">
    <div className="comparison-heading"><strong>声の検出器を比較</strong><div className="button-row">
      {ready ? <button disabled={locked} onClick={onAnalyze}>AST / YAMNet を比較</button> : <button disabled={locked} onClick={onSetup}>YAMNetをセットアップ</button>}
    </div></div>
    <p className="muted">原曲・分離ボーカルを別々に比較します。保存済みのMel-Bandボーカルも対象です。通常の「声の表現」と手修正は保持します。</p>
    {data && <details open><summary>保存した比較結果{data.runId ? ` · ${data.runId}` : ""}</summary>
      <p className="muted">{data.notice}</p>
      <label className="comparison-category">比較する声<select aria-label="比較する声" value={category} onChange={e => setCategory(e.target.value as ComparisonCategory)}>
        {(["beatbox", "breath", "humming"] as const).map(c => <option key={c} value={c}>{VOCAL_CATEGORIES[c]}</option>)}
      </select></label>
      <div className="comparison-scroll"><div style={{ width: width + 160 }}>
        <div className="comparison-lane"><div className="comparison-label">時間</div><svg width={width} height={26} aria-label="比較の時間軸">{Array.from({ length: Math.ceil(duration / 10) }, (_, i) => i * 10).map(t => <text key={t} x={t / duration * width + 3} y={18}>{timeLabel(t)}</text>)}</svg></div>
        {variants.map(variant => {
          const threshold = variant.thresholds[category];
          const rows = variant.candidates.filter(r => r.category === category);
          const peak = Math.max(0, ...variant.frames.map(f => f.scores[category]));
          const points = variant.frames.map(frame => `${(frame.start + frame.end) / 2 / duration * width},${66 - frame.scores[category] * 56}`).join(" ");
          return <div className="comparison-lane" key={variant.id}>
            <div className="comparison-label"><strong>{names(variant)}</strong><small>窓 {variant.windowSeconds}秒 / 刻み {variant.hopSeconds}秒</small><small>最大 {peak.toFixed(4)} · 候補 {rows.length}件</small></div>
            <svg width={width} height={96} aria-label={`${names(variant)} ${VOCAL_CATEGORIES[category]} スコア`}>
              <text x={3} y={12}>1</text><text x={3} y={66}>0</text>
              <line x1={0} x2={width} y1={66 - threshold.onset * 56} y2={66 - threshold.onset * 56} stroke="#f9c977" strokeDasharray="4 4" />
              <polyline points={points} stroke={variant.model === "yamnet" ? "#aeabff" : "#74d6b4"} strokeWidth={1.5} fill="none" />
              {variant.frames.map((frame, i) => <rect key={i} x={frame.start / duration * width} y={0} width={Math.max(2, variant.hopSeconds / duration * width)} height={70} fill="transparent" onClick={() => onAudition(variant.source, frame.start, frame.end)}>
                <title>{timeLabel(frame.start)}～{timeLabel(frame.end)} / {frame.scores[category].toFixed(4)}{category === "breath" ? " / " + Object.entries(frame.classScores).filter(([k]) => ["Breathing", "Gasp", "Pant", "Sigh"].includes(k)).map(([k, v]) => `${k}: ${v.toFixed(4)}`).join(", ") : ""}</title>
              </rect>)}
              {rows.map(row => <rect key={row.id} x={row.start! / duration * width} y={74} height={12} width={Math.max(2, (row.end! - row.start!) / duration * width)} fill="#aeabff" role="button" tabIndex={0}
                aria-label={`${names(variant)} ${row.label} ${timeLabel(row.start!)}を試聴区間に設定`} onClick={() => onAudition(variant.source, row.start!, row.end!)}
                onKeyDown={e => { if (e.key === "Enter") onAudition(variant.source, row.start!, row.end!); }}><title>{row.warning}</title></rect>)}
              <line x1={time / duration * width} x2={time / duration * width} y1={0} y2={96} stroke="white" opacity={.8} />
            </svg>
          </div>;
        })}
      </div></div>
      <p className="muted">縦軸0～1。破線は開始しきい値、下の帯は候補範囲です。グラフをクリックすると、その音声と解析窓を試聴区間に設定します。再生ボタンで確認してください。</p>
      <label className="comparison-category">候補一覧<select aria-label="候補一覧" value={selected?.id ?? ""} onChange={e => setSelectedVariant(e.target.value)}>{variants.map(v => <option key={v.id} value={v.id}>{names(v)}</option>)}</select></label>
      {selected && <p className="muted">開始 {selected.thresholds[category].onset} / 継続 {selected.thresholds[category].offset} · すべて要確認</p>}
      <div className="comparison-candidates">{candidates.map(row => <button key={row.id} onClick={() => onAudition(selected!.source, row.start!, row.end!)}>{timeLabel(row.start!)}～{timeLabel(row.end!)} · {row.score?.toFixed(4)}</button>)}</div>
      {!candidates.length && <p className="muted">この条件で候補はありません。対象の声が存在しないという判定ではありません。</p>}
    </details>}
  </section>;
}
