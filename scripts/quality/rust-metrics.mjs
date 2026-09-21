import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, readdirSync, writeFileSync, rmSync } from "node:fs";
import path from "node:path";
import { tmpdir } from "node:os";
import config from "../../quality-gate.config.mjs";

function number(value, label) {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`Missing/invalid Rust metric: ${label}`);
  return value;
}
export function evaluateRustUnit(unit, file) {
  const violations = [];
  const check = (space, symbol, metric, value, direction = "max") => {
    const actual = number(value, `${file}:${symbol}:${metric}`);
    const limit = config.rust[metric];
    if (direction === "min" ? actual < limit : actual > limit) {
      violations.push({ file, symbol, metric, actual, limit, direction, line: space.start_line });
    }
  };
  check(unit, "file", "maintainability", unit.metrics?.mi?.mi_visual_studio, "min");
  function visit(space, parent) {
    const symbol = `${parent}/${space.name}`;
    if (space.kind === "function") {
      const m = space.metrics;
      for (const [metric, actual] of Object.entries({ cognitive: m?.cognitive?.sum,
        cyclomatic: m?.cyclomatic?.sum, arguments: m?.nargs?.total,
        exits: m?.nexits?.sum, lines: m?.loc?.sloc })) check(space, symbol, metric, actual);
    }
    for (const child of space.spaces ?? []) visit(child, symbol);
  }
  for (const child of unit.spaces ?? []) visit(child, "");
  return violations;
}

export function rustMetrics(files) {
  const command = process.platform === "win32" ? "rust-code-analysis-cli.exe" : "rust-code-analysis-cli";
  const version = execFileSync(command, ["--version"], { encoding: "utf8" });
  if (!version.trim().endsWith(` ${config.tools.metrics}`)) throw new Error("Run npm run setup:quality: Rust metrics version mismatch");
  // The analyzer respects .gitignore, so sources must be outside ignored test-results.
  const temp = mkdtempSync(path.join(tmpdir(), "sweeper-quality-metrics-"));
  try {
    const source = path.join(temp, "source");
    const output = path.join(temp, "output");
    mkdirSync(output);
    const names = new Map();
    for (const [file, text] of files) {
      if (!file.startsWith("src-tauri/src/") || !file.endsWith(".rs")) continue;
      const target = path.join(source, file);
      mkdirSync(path.dirname(target), { recursive: true });
      writeFileSync(target, text);
      names.set(path.resolve(target).replaceAll("\\", "/"), file);
    }
    if (!names.size) throw new Error("No Rust source files found");
    execFileSync(command, ["-m", "-p", "source", "-O", "json", "-o", "output"], { cwd: temp, stdio: "pipe" });
    const units = readdirSync(output, { recursive: true }).filter((name) => name.endsWith(".json"))
      .map((name) => JSON.parse(readFileSync(path.join(output, name), "utf8")));
    const seen = new Set();
    const violations = units.flatMap((unit) => {
      const file = names.get(path.resolve(temp, unit.name).replaceAll("\\", "/"));
      if (!file || seen.has(file)) throw new Error(`Unexpected/duplicate Rust report: ${unit.name}`);
      seen.add(file);
      return evaluateRustUnit(unit, file);
    });
    if (seen.size !== names.size) throw new Error(`Incomplete Rust metrics output: ${seen.size}/${names.size}`);
    return violations;
  } finally {
    if (path.dirname(temp) !== path.resolve(tmpdir())) throw new Error("Unexpected temporary path");
    rmSync(temp, { recursive: true, force: true });
  }
}
