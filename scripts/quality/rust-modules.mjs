export function moduleCycles(dot) {
  if (!dot.trim().startsWith("digraph {") || !dot.trim().endsWith("}")) throw new Error("Invalid Rust dependency graph");
  const modules = [...dot.matchAll(/^\s*"([^"]+)" \[.*; \/\/ "(?:crate|mod)" node$/gm)]
    .map((match) => match[1]).sort((a, b) => b.length - a.length);
  if (!modules.length) throw new Error("Rust graph contains no modules");
  const owner = (name) => modules.find((module) => name === module || name.startsWith(`${module}::`));
  const graph = new Map(modules.map((module) => [module, new Set()]));
  for (const match of dot.matchAll(/^\s*"([^"]+)" -> "([^"]+)" .*; \/\/ "uses" edge$/gm)) {
    const from = owner(match[1]);
    const to = owner(match[2]);
    if (!from || !to) throw new Error("Rust dependency has no owning module");
    if (from !== to) graph.get(from).add(to);
  }
  const visited = new Set();
  const cycles = [];
  function visit(module, stack) {
    if (stack.includes(module)) {
      cycles.push([...stack.slice(stack.indexOf(module)), module].join(" -> "));
      return;
    }
    if (visited.has(module)) return;
    visited.add(module);
    for (const next of graph.get(module)) visit(next, [...stack, module]);
  }
  for (const module of modules) visit(module, []);
  return cycles;
}
