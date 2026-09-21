import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

export const sourcePattern = /\.(?:[cm]?[jt]sx?|rs|py|css|ps1)$/;
export function sourceFiles(root, staged = false) {
  const args = staged ? ["ls-files", "-z"] : ["ls-files", "-z", "--cached", "--others", "--exclude-standard"];
  const names = execFileSync("git", args, { cwd: root, encoding: "utf8" }).split("\0");
  const files = new Map();
  for (const name of new Set(names.filter((name) => sourcePattern.test(name)))) {
    try {
      const text = staged
        ? execFileSync("git", ["show", `:${name}`], { cwd: root, encoding: "utf8" })
        : readFileSync(`${root}/${name}`, "utf8");
      files.set(name, text);
    } catch (error) {
      if (!staged && error.code === "ENOENT") continue;
      throw error;
    }
  }
  return files;
}

export function lineCount(text) {
  if (!text) return 0;
  return text.replace(/\r\n/g, "\n").replace(/\n$/, "").split("\n").length;
}
