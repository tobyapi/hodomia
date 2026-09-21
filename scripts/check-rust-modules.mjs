import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { moduleCycles } from "./quality/rust-modules.mjs";

const dot = execFileSync("cargo", ["modules", "dependencies", "--manifest-path", "src-tauri/Cargo.toml",
  "--lib", "--no-externs", "--no-sysroot"], { encoding: "utf8", maxBuffer: 16 * 1024 * 1024 });
mkdirSync("test-results", { recursive: true });
writeFileSync("test-results/rust-modules.dot", dot);
const cycles = moduleCycles(dot.replaceAll("\r\n", "\n"));
for (const cycle of cycles) console.error(`Rust module cycle: ${cycle}`);
console.log(`Rust module cycles: ${cycles.length}`);
if (cycles.length) process.exitCode = 1;
