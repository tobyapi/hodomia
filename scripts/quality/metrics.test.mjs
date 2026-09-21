import { test } from "node:test";
import assert from "node:assert/strict";
import { compareBaseline, metricSnapshot, baselineExpansions } from "./baseline.mjs";
import { evaluateRustUnit, rustMetrics } from "./rust-metrics.mjs";
import { typescriptMetrics } from "./typescript-metrics.mjs";

const violation = (actual, direction = "max", symbol = "one") => ({
  file: "sample", symbol, metric: "complexity", direction, actual,
});
test("baseline rejects new symbols, extra violations, growth and MI deterioration", () => {
  const baseline = metricSnapshot([violation(12), violation(35, "min")]);
  assert.equal(compareBaseline([violation(13)], baseline).errors.length, 1);
  assert.equal(compareBaseline([violation(34, "min")], baseline).errors.length, 1);
  assert.equal(compareBaseline([violation(12, "max", "new")], baseline).errors.length, 1);
  assert.equal(compareBaseline([violation(12), violation(12)], baseline).errors.length, 1);
  assert.equal(compareBaseline([violation(12), violation(35, "min")], baseline).stale, false);
});
test("improvements must shrink baseline and old allowances cannot be expanded", () => {
  const baseline = metricSnapshot([violation(12)]);
  const improved = compareBaseline([violation(11)], baseline);
  assert.deepEqual(improved.errors, []);
  assert.equal(improved.stale, true);
  assert.equal(compareBaseline([], baseline).stale, true);
  assert.equal(baselineExpansions(baseline, improved.current).length, 1);
  assert.deepEqual(baselineExpansions(improved.current, baseline), []);
});
function unit(mi = 40, cognitive = 15) {
  return { start_line: 1, metrics: { mi: { mi_visual_studio: mi } }, spaces: [{
    kind: "function", name: "f", start_line: 1, spaces: [],
    metrics: { cognitive: { sum: cognitive }, cyclomatic: { sum: 10 }, nargs: { total: 5 },
      nexits: { sum: 5 }, loc: { sloc: 80 } },
  }] };
}
test("Rust accepts limits exactly, rejects below MI40 and missing measurements", () => {
  assert.deepEqual(evaluateRustUnit(unit(), "file.rs"), []);
  assert.equal(evaluateRustUnit(unit(39, 16), "file.rs").length, 2);
  assert.throws(() => evaluateRustUnit(unit(null), "file.rs"), /invalid Rust metric/);
});
test("TypeScript uses real ESLint metrics, including numeric function names", async () => {
  const text = `/* eslint-disable complexity */\nexport function case999(x: number) { ${"if (x) x--; ".repeat(11)} return x; }`;
  const result = await typescriptMetrics(new Map([["src/example.ts", text]]), process.cwd());
  const complexity = result.find((v) => v.metric === "complexity");
  assert.equal(complexity.actual, 12);
  assert.equal(complexity.symbol, "case999");
});
test("Rust tool measures supplied snapshot text, including nested source paths", () => {
  const result = rustMetrics(new Map([["src-tauri/src/nested/example.rs",
    `pub fn example(x: i32) { ${"if x > 0 { println!(\"yes\"); } ".repeat(16)} }`]]));
  assert.ok(result.some((v) => v.metric === "cyclomatic" && v.actual > 10));
  assert.ok(result.every((v) => v.file === "src-tauri/src/nested/example.rs"));
});
