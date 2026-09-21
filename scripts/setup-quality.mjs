import { execFileSync } from "node:child_process";
import config from "../quality-gate.config.mjs";

for (const [name, version] of [["cargo-modules", config.tools.modules], ["rust-code-analysis-cli", config.tools.metrics]]) {
  execFileSync("cargo", ["install", "--locked", "--version", version, name], { stdio: "inherit" });
}
