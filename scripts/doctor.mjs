import { spawnSync } from "node:child_process";

const commands = [["node", ["--version"]], ["rustc", ["--version"]], ["cargo", ["--version"]], ["rustup", ["show", "active-toolchain"]]];
let failed = false;
for (const [command, args] of commands) {
  const result = spawnSync(command, args, { encoding: "utf8" });
  console.log(`${command}: ${result.error?.message ?? (result.stdout + result.stderr).trim()}`);
  if (result.error || result.status !== 0) failed = true;
}
const cli = spawnSync(process.execPath, ["node_modules/@tauri-apps/cli/tauri.js", "info"], { stdio: "inherit" });
if (cli.status !== 0) failed = true;
process.exitCode = failed ? 1 : 0;
