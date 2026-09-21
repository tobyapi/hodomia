import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { boundaryErrors } from "./boundaries.mjs";
import { lineCount, sourceFiles } from "./source-files.mjs";

const check = (entries) => boundaryErrors(new Map(entries));
test("physical lines include comments and blanks but not final newline", () => {
  assert.equal(lineCount(""), 0);
  assert.equal(lineCount("a\r\n\r\n// comment\r\n"), 3);
  assert.equal(lineCount("x\n".repeat(150)), 150);
  assert.equal(lineCount("x\n".repeat(151)), 151);
});
test("native calls and reverse dependencies are rejected, comments ignored", () => {
  assert.equal(check([["src/components/A.tsx", '// import x from "@tauri-apps/api/core";']]).length, 0);
  for (const text of ['import {invoke} from "@tauri-apps/api/core";',
    'export * from "../api";', 'const x = import("../api");']) {
    assert.ok(check([["src/components/A.tsx", text]]).length);
  }
  assert.ok(check([["src/editing.ts", 'import React from "react";']]).length);
  assert.equal(check([["src/api.ts", 'import {invoke} from "@tauri-apps/api/core";']]).length, 0);
});
test("production cannot import test code and cycles are detected", () => {
  assert.ok(check([["src/A.ts", 'import x from "./A.test";']]).length);
  assert.ok(check([["src/a.ts", 'import "./b";'], ["src/b.ts", 'export * from "./a";']])
    .some((message) => message.includes("cycle")));
});
test("Rust library stays independent and ML remains in worker", () => {
  assert.ok(check([["src-tauri/src/library.rs", "use crate::workspace::grant;"]]).length);
  assert.ok(check([["src-tauri/src/model.rs", "use tch::{Tensor};"]]).length);
  assert.equal(check([["src-tauri/src/library.rs", '// tauri::State\nlet x = "workspace::grant";']]).length, 0);
});
test("staged snapshot ignores unstaged edits; new and deleted files handled", () => {
  const root = mkdtempSync(path.join(tmpdir(), "sweeper-quality-"));
  const git = (...args) => execFileSync("git", args, { cwd: root, stdio: "pipe" });
  try {
    git("init");
    writeFileSync(path.join(root, "sample.ts"), "staged\n");
    git("add", "sample.ts");
    writeFileSync(path.join(root, "sample.ts"), "working\n");
    writeFileSync(path.join(root, "new.rs"), "new\n");
    assert.equal(sourceFiles(root, true).get("sample.ts"), "staged\n");
    assert.equal(sourceFiles(root).get("sample.ts"), "working\n");
    assert.equal(sourceFiles(root).get("new.rs"), "new\n");
    assert.equal(sourceFiles(root, true).has("new.rs"), false);
    git("rm", "--cached", "-f", "sample.ts");
    assert.equal(sourceFiles(root, true).has("sample.ts"), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
