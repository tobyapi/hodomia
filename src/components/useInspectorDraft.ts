import { useEffect, useState } from "react";
import { validRow } from "../editing";
import type { TimelineRow, Track, VocalCategory } from "../types";

function initial(row: TimelineRow) {
  return {
    label: row.label, category: row.category ?? "other" as VocalCategory,
    start: row.start?.toString() ?? "", end: row.end?.toString() ?? "", reviewed: row.reviewed ?? false
  };
}
export function useInspectorDraft(row: TimelineRow, track: Track, duration: number,
  onSave: (row: TimelineRow) => void, onDirtyChange?: (dirty: boolean) => void) {
  const [draft, setDraft] = useState(() => initial(row));
  const [error, setError] = useState("");
  const original = initial(row);
  const dirty = (Object.keys(original) as (keyof typeof original)[]).some(key => draft[key] !== original[key]);
  useEffect(() => { onDirtyChange?.(dirty); return () => onDirtyChange?.(false); }, [dirty, onDirtyChange]);
  function save() {
    const { label, start, end, reviewed, category } = draft;
    const value = {
      ...row, label, start: start === "" ? null : Number(start), end: end === "" ? null : Number(end), reviewed,
      ...(track === "vocalEvents" ? { category } : {})
    };
    const problem = validRow(value, track, duration);
    if (problem) { setError(problem); return; }
    onSave(value); setError("");
  }
  const update = (values: Partial<typeof draft>) => setDraft(current => ({ ...current, ...values }));
  return {
    ...draft, error, save, setLabel: (label: string) => update({ label }),
    setCategory: (category: VocalCategory) => update({ category }), setStart: (start: string) => update({ start }),
    setEnd: (end: string) => update({ end }), setReviewed: (reviewed: boolean) => update({ reviewed })
  };
}
