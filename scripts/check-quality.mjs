import { fileURLToPath } from "node:url";
import { sourceFiles, lineCount } from "./quality/source-files.mjs";
import { boundaryErrors } from "./quality/boundaries.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));
const args = process.argv.slice(2);
if (args.some((arg) => !["--staged", "--strict-length"].includes(arg))) {
  throw new Error("Usage: check-quality.mjs [--staged] [--strict-length]");
}
const files = sourceFiles(root, args.includes("--staged"));
const longFiles = [...files].map(([file, text]) => ({ file, lines: lineCount(text) }))
  .filter(({ lines }) => lines > 150).sort((a, b) => b.lines - a.lines);
for (const { file, lines } of longFiles) console.warn(`WARN ${file}: ${lines} lines (guideline: 150; review responsibility boundaries)`);
const errors = boundaryErrors(files);
for (const error of errors) console.error(`ERROR ${error}`);
console.log(`Quality: ${files.size} source files, ${longFiles.length} length warnings, ${errors.length} boundary errors.`);
if (errors.length || (longFiles.length && args.includes("--strict-length"))) process.exitCode = 1;
