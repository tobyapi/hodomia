import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { sourceFiles } from "./quality/source-files.mjs";
import { typescriptMetrics } from "./quality/typescript-metrics.mjs";
import { rustMetrics } from "./quality/rust-metrics.mjs";
import { baselineExpansions, compareBaseline, metricSnapshot, validateBaseline } from "./quality/baseline.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));
const args = process.argv.slice(2);
const staged = args.includes("--staged");
if (args.some((a) => !["--staged", "--init-baseline", "--prune-baseline", "--strict"].includes(a))
  || args.length > 1) throw new Error("Usage: check-metrics.mjs [--staged|--init-baseline|--prune-baseline|--strict]");
const baselineFile = ".clean/quality-baseline.json";
const reportFile = `${root}/test-results/quality-metrics${staged ? "-staged" : ""}.json`;
mkdirSync(`${root}/test-results`, { recursive: true });
try {
  if (staged) {
    execFileSync("git", ["diff", "--exit-code", "--", "package.json", "package-lock.json",
      "eslint.config.js", "quality-gate.config.mjs", "scripts/quality", "scripts/check-metrics.mjs"], { cwd: root, stdio: "pipe" });
  }
  const files = sourceFiles(root, staged);
  const violations = [...await typescriptMetrics(files, root), ...rustMetrics(files)];
  if (args.includes("--init-baseline")) {
    if (existsSync(`${root}/${baselineFile}`)) throw new Error("Baseline already exists; it cannot be regenerated");
    writeFileSync(`${root}/${baselineFile}`, `${JSON.stringify(metricSnapshot(violations), null, 2)}\n`);
  }
  const baselineText = staged
    ? execFileSync("git", ["show", `:${baselineFile}`], { cwd: root, encoding: "utf8" })
    : readFileSync(`${root}/${baselineFile}`, "utf8");
  const baseline = validateBaseline(JSON.parse(baselineText));
  const tracked = execFileSync("git", ["ls-tree", "--name-only", "HEAD", baselineFile], { cwd: root, encoding: "utf8" }).trim();
  if (tracked) {
    const previous = JSON.parse(execFileSync("git", ["show", `HEAD:${baselineFile}`], { cwd: root, encoding: "utf8" }));
    const expansions = baselineExpansions(baseline, validateBaseline(previous));
    if (expansions.length) throw new Error(`Baseline cannot grow:\n${expansions.join("\n")}`);
  }
  const result = compareBaseline(violations, baseline);
  if (args.includes("--prune-baseline") && !result.errors.length) {
    writeFileSync(`${root}/${baselineFile}`, `${JSON.stringify(result.current, null, 2)}\n`);
    result.stale = false;
  }
  if (result.stale && !result.errors.length) result.errors.push("Improved metrics: run npm run quality:prune, then stage the reduced baseline");
  if (args.includes("--strict") && violations.length) result.errors.push("Strict mode rejects existing violations too");
  for (const v of violations) console.warn(`DEBT ${v.file}:${v.line} ${v.symbol}: ${v.metric}=${v.actual} (target ${v.direction} ${v.limit})`);
  for (const error of result.errors) console.error(`ERROR ${error}`);
  const passed = result.errors.length === 0;
  writeFileSync(reportFile, `${JSON.stringify({ passed, staged, violations, errors: result.errors }, null, 2)}\n`);
  console.log(`Metrics: ${violations.length} existing violations; ${result.errors.length} errors. ${reportFile}`);
  if (!passed) process.exitCode = 1;
} catch (error) {
  writeFileSync(reportFile, `${JSON.stringify({ passed: false, error: error.message }, null, 2)}\n`);
  console.error(error);
  process.exitCode = 1;
}
