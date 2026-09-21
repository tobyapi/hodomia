import type { Point } from "../types";

function append(paths: string[], current: string) { if (current) paths.push(current); }

export function Curve({ points, duration, width, color, pitch = false }: { points: Point[]; duration: number; width: number; color: string; pitch?: boolean }) {
  const paths: string[] = [];
  let current = "";
  for (const p of points) {
    if (p.value === null) { append(paths, current); current = ""; continue; }
    const height = pitch ? Math.max(0, Math.min(1, (p.value - 36) / 60)) : Math.max(0, Math.min(1, p.value));
    current += (current ? " L" : "M") + (p.time / duration * width).toFixed(1) + " " + (66 - height * 54).toFixed(1);
  }
  if (current) paths.push(current);
  return <>{paths.map((d, i) => <path key={i} d={d} stroke={color} strokeWidth={1.5} fill="none" />)}</>;
}

