import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const cwd = fileURLToPath(new URL("../", import.meta.url));
if (process.env.CI) {
  console.log("CI: hooks skipped; npm run check runs the same quality checks.");
} else {
  let current = "";
  try {
    current = execFileSync("git", ["config", "--get", "core.hooksPath"], { cwd, encoding: "utf8" }).trim();
  } catch (error) {
    if (error.status !== 1) throw error;
  }
  if (current && current !== ".githooks") throw new Error(`Existing hooksPath preserved: ${current}. Integrate .githooks/pre-commit manually.`);
  execFileSync("git", ["config", "--local", "core.hooksPath", ".githooks"], { cwd });
  console.log("Installed .githooks/pre-commit (staged metrics) and pre-push (full analysis).");
}
