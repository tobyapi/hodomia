import parser from "@typescript-eslint/parser";
import sonarjs from "eslint-plugin-sonarjs";
import config from "./quality-gate.config.mjs";

const limits = config.typescript;
export default [{
  files: ["src/**/*.{ts,tsx}"],
  languageOptions: { parser },
  plugins: { sonarjs },
  rules: {
    complexity: ["error", limits.cyclomatic],
    "max-depth": ["error", limits.depth],
    "max-lines-per-function": ["error", { max: limits.lines, skipBlankLines: true, skipComments: true }],
    "max-statements": ["error", limits.statements],
    "sonarjs/cognitive-complexity": ["error", limits.cognitive],
  },
}];
