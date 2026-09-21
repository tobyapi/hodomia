import ts from "typescript";
import path from "node:path";

function imports(file, text) {
  const result = [];
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true);
  function visit(node) {
    if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier) {
      if (ts.isStringLiteral(node.moduleSpecifier)) result.push(node.moduleSpecifier.text);
    }
    if (ts.isCallExpression(node) && (node.expression.kind === ts.SyntaxKind.ImportKeyword
      || node.expression.getText(source) === "require") && node.arguments.length === 1
      && ts.isStringLiteral(node.arguments[0])) result.push(node.arguments[0].text);
    ts.forEachChild(node, visit);
  }
  visit(source);
  return result;
}

const testFile = (file) => /(?:\.test(?:\.|$)|\/test\/)/.test(file);
export function boundaryErrors(files) {
  const errors = [];
  const graph = new Map();
  for (const [file, text] of files) {
    const fail = (message) => errors.push(`${file}: ${message}`);
    if (file.startsWith("src/") && /\.tsx?$/.test(file) && !testFile(file)) {
      const edges = [];
      for (const specifier of imports(file, text)) {
        const target = specifier.startsWith(".")
          ? path.posix.normalize(path.posix.join(path.posix.dirname(file), specifier)) : specifier;
        const resolved = [target, `${target}.ts`, `${target}.tsx`, `${target}/index.ts`, `${target}/index.tsx`]
          .find((candidate) => files.has(candidate));
        if (resolved) edges.push(resolved);
        if (specifier.startsWith("@tauri-apps/") && !["src/api.ts", "src/useCloseSave.ts"].includes(file)) {
          fail(`native API must stay in api.ts / useCloseSave.ts: ${specifier}`);
        }
        if (/^(node:|fs$|child_process$)|(^|\/)(analysis|automation|tests|src-tauri)\//.test(target)
          || testFile(target) || /^(vitest|@testing-library)/.test(target)) {
          fail(`production UI must not depend on runtime/test implementation: ${specifier}`);
        }
        if (["src/types.ts", "src/editing.ts"].includes(file)
          && !["src/types", "src/types.ts"].includes(target)) {
          fail(`pure data/editing module must only depend on types: ${specifier}`);
        }
        if (file.startsWith("src/components/") && /src\/(App|api|useCloseSave)(\.|$)/.test(target)) {
          fail(`view must receive application operations through props: ${specifier}`);
        }
        if (file === "src/api.ts" && !specifier.startsWith("@tauri-apps/")
          && !["src/types", "src/types.ts"].includes(target)) fail(`IPC adapter dependency: ${specifier}`);
      }
      graph.set(file, edges);
    }
    if (file.startsWith("src-tauri/src/") && file.endsWith(".rs")) {
      // Lexical guard, not a Rust type/semantic analysis. Strip comments and string literals.
      const code = text.replace(/\/\*[\s\S]*?\*\/|\/\/[^\n]*|r(\#*)"[\s\S]*?"\1|"(?:\\.|[^"\\])*"/g, " ");
      if (/\b(pyo3|tch|candle_core|ort)\s*(?:::|[,;}])/.test(code)) fail("ML inference belongs in Python workers");
      if (file === "src-tauri/src/library.rs" && /\b(tauri|workspace)\s*(?:::|[,;}])/.test(code)) {
        fail("project library must not depend on Tauri commands/workspace");
      }
    }
  }
  const visited = new Set();
  function walk(file, stack) {
    if (stack.includes(file)) {
      errors.push(`dependency cycle: ${[...stack.slice(stack.indexOf(file)), file].join(" -> ")}`);
      return;
    }
    if (visited.has(file)) return;
    visited.add(file);
    for (const next of graph.get(file) ?? []) walk(next, [...stack, file]);
  }
  for (const file of graph.keys()) walk(file, []);
  return errors;
}
