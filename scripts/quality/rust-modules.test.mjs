import { test } from "node:test";
import assert from "node:assert/strict";
import { moduleCycles } from "./rust-modules.mjs";

const node = (name, kind) => `"${name}" [label="${kind}"]; // "${kind}" node`;
const edge = (from, to, kind = "uses") => `"${from}" -> "${to}" [label="${kind}"]; // "${kind}" edge`;
const graph = (...edges) => `digraph {\n${[
  node("app", "crate"), node("app::a", "mod"), node("app::b", "mod"), ...edges,
].join("\n")}\n}`;
test("Rust checks inter-module cycles, ignoring struct ownership and intra-module recursion", () => {
  assert.deepEqual(moduleCycles(graph(edge("app::a::S", "app::a::S::drop", "owns"),
    edge("app::a::S::drop", "app::a::S"))), []);
  assert.deepEqual(moduleCycles(graph(edge("app::a::f", "app::b::S"))), []);
  assert.equal(moduleCycles(graph(edge("app::a::f", "app::b::S"), edge("app::b::f", "app::a::S"))).length, 1);
  assert.throws(() => moduleCycles(""), /Invalid/);
  assert.throws(() => moduleCycles("digraph {\n}"), /no modules/);
});
