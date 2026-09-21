export default {
  forbidden: [
    { name: "no-circular", severity: "error", from: {}, to: { circular: true } },
    { name: "no-unresolved", severity: "error", from: {}, to: { couldNotResolve: true } },
    {
      name: "no-orphans", severity: "error",
      from: { orphan: true, pathNot: ["^src/main\\.tsx$", "\\.test\\.", "^src/test/", "\\.d\\.ts$"] }, to: {},
    },
    {
      name: "views-use-props", severity: "error", from: { path: "^src/components/" },
      to: { path: "^src/(App|api|useCloseSave)\\." },
    },
    {
      name: "pure-editing", severity: "error", from: { path: "^src/(types|editing)\\.ts$" },
      to: { pathNot: "^src/types\\.ts$" },
    },
    {
      name: "native-api-boundary", severity: "error",
      from: { path: "^src/", pathNot: ["^src/(api|useCloseSave)\\.ts$", "\\.test\\.", "^src/test/"] },
      to: { path: "(^|/)@tauri-apps/" },
    },
    {
      name: "no-test-in-production", severity: "error",
      from: { path: "^src/", pathNot: ["\\.test\\.", "^src/test/"] },
      to: { path: "(\\.test\\.|^src/test/|(^|/)(vitest|@testing-library)/)" },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
    enhancedResolveOptions: { exportsFields: ["exports"], conditionNames: ["import", "types", "default"] },
  },
};
