import { mkdir, readFile, writeFile, copyFile } from "node:fs/promises";
import { resolve, join, basename, relative, isAbsolute } from "node:path";

const root = resolve(process.argv[2] ?? "");
if (!process.argv[2]) throw new Error("Usage: npm run harness:prepare -- <project-folder>");
function within(path) {
  const target = resolve(root, path), diff = relative(root, target);
  if (diff.startsWith("..") || isAbsolute(diff)) throw new Error("Project path escapes root");
  return target;
}
const json = async path => JSON.parse(await readFile(path, "utf8"));
const project = await json(join(root, "project.json"));
const edits = await json(join(root, "edits.json"));
const run = within("runs/" + project.currentRun);
const result = await json(join(run, "result.json"));
const status = await json(join(run, "status.json"));
await mkdir("test-results/ui-media", { recursive: true });
await copyFile(within(project.audio), "test-results/ui-media/original.wav");
for (const path of Object.values({ ...result.stems, ...result.separationComparison?.stems })) await copyFile(within(path), join("test-results/ui-media", basename(path)));
await writeFile("test-results/ui-snapshot.json", JSON.stringify({ root, project, edits, result, status }));
console.log("Open http://127.0.0.1:1430/tests/ui/ with npm run dev running.");
