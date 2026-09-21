# Framework And Language Map

Use this reference when applying clean-code principles outside your strongest language. Keep the principle; adapt the implementation.

## Universal Rule

Clean code should look idiomatic to a senior maintainer of that stack.

## Languages

| Stack | Clean Code Usually Means | Watch For |
| --- | --- | --- |
| JavaScript and TypeScript | narrow types, clear async flow, explicit data shapes, predictable module boundaries | `any`, promise chains that hide errors, over-generic helpers, framework logic in utilities |
| Python | readable names, simple functions, explicit exceptions, small modules, type hints where useful | mutable defaults, broad `except`, implicit `None`, hidden I/O in helpers |
| Go | small functions, errors with context, interfaces at consumers, explicit dependencies | premature abstractions, package-level state, ignored errors, giant structs |
| Java, Kotlin, C# | cohesive classes, clear domain services, dependency injection with restraint, typed boundaries | manager/service sprawl, anemic models, deep inheritance, null ambiguity |
| Rust | invariants in types, ownership-driven design, explicit error types, small modules | cloning to appease borrow errors, `unwrap` in production paths, over-wide traits |
| Swift | value semantics when useful, clear async and actor boundaries, expressive names | force unwraps, implicit main-thread assumptions, massive view models |
| PHP and Ruby | clear domain names, framework conventions, small service objects only when needed | callbacks hiding behavior, dynamic magic without tests, fat models/controllers |
| C and C++ | ownership clarity, RAII where available, narrow interfaces, explicit lifetimes | raw ownership ambiguity, unchecked return codes, macro cleverness, data races |
| Shell | quoted variables, strict modes when safe, linear flow, clear exit behavior | unquoted expansion, ignored failures, complex parsing, hidden environment dependencies |
| SQL | set-based logic, clear aliases, named CTEs, explicit transactions | string-built queries, ambiguous joins, N+1 access, missing indexes for changed access patterns |

## Frameworks And Domains

| Area | Clean Code Usually Means | Watch For |
| --- | --- | --- |
| React and frontend UI | predictable rendering, state close to use, separated effects, accessible components | large components, derived state drift, effect dependency bugs, inaccessible custom controls |
| Backend APIs | validation at boundaries, stable contracts, clear status/error models, focused handlers | business logic in controllers, leaky persistence models, inconsistent errors |
| Mobile | lifecycle-aware state, explicit permissions, responsive UI work, offline/error states | hidden lifecycle coupling, blocking main thread, platform assumptions |
| Data and ML | reproducible pipelines, explicit schemas, deterministic transforms, experiment metadata | notebook-only logic, silent data coercion, train/serve skew |
| Infrastructure as code | named resources, least privilege, explicit dependencies, safe defaults | copy-paste resources, wildcard permissions, hidden environment coupling |
| Tests | behavior names, readable fixtures, deterministic setup and teardown | broad snapshots, sleeps, excessive mocks, tests that assert implementation details |

## Where Files Live Per Ecosystem

Placement conventions differ by stack. Before creating a file, check what the ecosystem and the specific project expect:

| Ecosystem | Typical Expectations |
| --- | --- |
| Node/TypeScript | sources under `src/`, tests alongside (`*.test.ts`) or under `__tests__/`, barrels only where the project already uses them, path aliases from tsconfig |
| Python | package directories with `__init__.py`, tests under `tests/` mirroring package paths, modules snake_case |
| Go | one package per directory, package name matches directory, tests as `*_test.go` beside sources, `internal/` for private packages |
| Java/Kotlin/C# | namespace and directory must agree, tests in a parallel source set, one public type per file where conventional |
| Rust | modules declared in `lib.rs`/`mod.rs`/`mod` statements — a file without a `mod` declaration is not compiled |
| React and frontend | components co-located with styles and tests per project pattern, route files where the framework's router expects them |
| Rails/Django/Laravel | framework directory conventions are load-bearing (autoloading, discovery); place files where the framework looks for them |
| Monorepos | respect package boundaries and each package's own conventions; never import across packages except through their public entry points |

In every case the specific project's existing layout overrides the ecosystem default.

## Adaptation Questions

Before changing code in an unfamiliar stack, ask:

1. What does this ecosystem consider idiomatic error handling?
2. Where should domain logic live in this framework?
3. Where do new files go, and what registration makes them reachable?
4. What formatter or linter owns style?
5. How are tests normally structured?
6. What boundaries are risky here: network, database, UI lifecycle, concurrency, generated code, or permissions?
7. Which local pattern is established, and is it safe enough to follow?
