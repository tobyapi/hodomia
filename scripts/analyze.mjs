import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import config from "../quality-gate.config.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));
const manifest = ["--manifest-path", "src-tauri/Cargo.toml"];
const gates = [
  ["source boundaries and length", process.execPath, ["scripts/check-quality.mjs"]],
  ["complexity and maintainability", process.execPath, ["scripts/check-metrics.mjs"]],
  ["TypeScript dependencies", process.execPath, ["node_modules/dependency-cruiser/bin/dependency-cruise.mjs", "src", "--config", "dependency-cruiser.config.mjs"]],
  ["Rust module tool", "cargo", ["modules", "--version"]],
  ["Rust cycles", process.execPath, ["scripts/check-rust-modules.mjs"]],
  ["Rust orphans", "cargo", ["modules", "orphans", ...manifest, "--lib", "--deny"]],
  ["Rust Clippy", "cargo", ["clippy", "--locked", ...manifest, "--all-targets", "--", "-D", "warnings"]],
];
const results = [];
for (const [name, command, args] of gates) {
  console.log(`RUN ${name}`);
  const start = Date.now();
  const result = spawnSync(command, args, { cwd: root, encoding: "utf8", maxBuffer: 16 * 1024 * 1024 });
  const versionMatches = name !== "Rust module tool" || result.stdout?.trim().endsWith(` ${config.tools.modules}`);
  const passed = !result.error && result.status === 0 && versionMatches;
  results.push({ name, passed, durationMs: Date.now() - start, exitCode: result.status,
    stdout: result.stdout, stderr: result.stderr, error: result.error?.message });
  if (!passed) console.error(result.error?.message ?? `${result.stdout}\n${result.stderr}\nCheck tool versions with npm run setup:quality.`);
  console.log(`${passed ? "PASS" : "FAIL"} ${name}`);
}
const passed = results.every((result) => result.passed);
mkdirSync(`${root}/test-results`, { recursive: true });
writeFileSync(`${root}/test-results/quality-gate.json`, `${JSON.stringify({ passed, results }, null, 2)}\n`);
console.log(`Report: ${root}/test-results/quality-gate.json`);
if (!passed) process.exitCode = 1;
