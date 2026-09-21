# Architecture Map

Routing table: the architectural question you are facing, and the rule that answers it. Use this to
find the right rule fast; the reasoning lives in `architecture.md`.

## By question

| The question in front of you | The rule that decides it |
| --- | --- |
| Where does this new module belong? | Level = distance from I/O. Business rules highest, delivery mechanisms lowest |
| May this file import that one? | The Dependency Rule: inward only, never outward |
| Two modules need each other | You have a cycle. Invert one edge, or extract a component both depend on |
| Where do I put the interface? | On the side that *uses* it. The API is owned by its user, not its implementer |
| Should this be one module or two? | Which actors can demand a change? Different actors, different modules |
| These two blocks look identical | Is it true duplication — must they always change together? If not, leave them apart |
| Should I add an abstraction here? | Only for a second implementation or a boundary you must protect now |
| Should this be a service? | Not for decoupling alone. A process boundary is not an architectural boundary |
| Which database / framework / UI? | A detail. Defer it, and design so the answer can change |
| The framework wants to be my base class | Refuse. Derive a proxy in an outer layer instead |
| Where does dependency injection go? | `main` only. Inject there, then pass dependencies onward normally |
| Where does SQL go? | The data-access layer, nowhere else |
| Can I pass this ORM object inward? | No. Define a structure per crossing and copy the fields |
| This code is hard to test | Split it. The untestable half must be humble: no decisions in it |
| How do I stop people bypassing a layer? | Access modifiers and one public entry point per component. Let the compiler enforce it |
| Should I build a full boundary? | Only at the inflection point where building it costs less than going without |
| Is this component too unstable to depend on? | `I = Fan-out / (Fan-in + Fan-out)`. `I` must decrease in the direction of dependency |
| Is this component badly balanced? | `D = \|A + I - 1\|`. Investigate above ~0.1 or beyond one standard deviation |
| A small requirement forced a large diff | An architecture defect. Scope should drive difficulty, never shape |
| The structure is a mess — rewrite it? | No. The team that made the mess rebuilds it. Refactor in verified batches |

## By topic

The named rules themselves now live in one place each, so this file does not restate them:

- **`canon.md`** — every named rule from both books with a one-line operational meaning. Start here
  when you know the name but not the rule.
- **`architecture.md`** — the reasoning, in this order: the dependency rule and level, the circles
  and boundary crossing, boundary costs and partial boundaries, SOLID as dependency rules, component
  cohesion and coupling with the metrics, keeping details out, systems and cross-cutting policy,
  testability, packaging and enforcement, decoupling modes, duplication.

## Reading order

Coming to this cold, in this order:

1. The Dependency Rule and level (`architecture.md`, first two sections) — decides most placement
   questions on its own.
2. SOLID as dependency rules — decides most module-shape questions.
3. Boundaries and their costs — decides when to separate and how far.
4. Packaging and enforcement — decides whether any of it survives contact with a deadline.
5. Component metrics — only when you need evidence rather than opinion.
