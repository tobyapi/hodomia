import { ESLint } from "eslint";
import ts from "typescript";

function symbolAt(file, text, line, column) {
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true);
  const position = source.getPositionOfLineAndCharacter(line - 1, column - 1);
  const names = [];
  function visit(node) {
    if (position < node.getStart(source) || position >= node.end) return;
    if (ts.isFunctionLike(node)) {
      const parent = node.parent;
      names.push(node.name?.getText(source) ?? (ts.isVariableDeclaration(parent)
        ? parent.name.getText(source) : ts.isCallExpression(parent)
          ? `${parent.expression.getText(source)} callback` : "anonymous"));
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  return names.join("/") || "module";
}

export async function typescriptMetrics(files, root) {
  const eslint = new ESLint({ cwd: root, allowInlineConfig: false });
  const violations = [];
  for (const [file, text] of files) {
    if (!/^src\/.*\.tsx?$/.test(file)) continue;
    const [result] = await eslint.lintText(text, { filePath: file });
    for (const message of result.messages) {
      if (message.fatal || !message.ruleId) throw new Error(`${file}: ${message.message}`);
      const values = message.message.match(/\d+/g)?.slice(-2).map(Number);
      if (!values || values.length < 2) throw new Error(`Unrecognized metric: ${message.message}`);
      violations.push({ file, symbol: symbolAt(file, text, message.line, message.column),
        metric: message.ruleId, actual: values[0], limit: values[1], direction: "max", line: message.line });
    }
  }
  return violations;
}
