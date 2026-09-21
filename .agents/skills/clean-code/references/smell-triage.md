# Smell Triage

A lookup table for deciding what to do about a smell you have found. The scope gate in `SKILL.md`
decides *whether* to act; this file says *what* the usual action is.

**The scope gate, restated:** fix it now only if it blocks the requested change, creates immediate
risk, or your own work introduced it. Otherwise report it separately without touching it. In
campaign mode, log it in the ledger and handle it in its batch.

Cite smell IDs from `chapter-map.md` (G17, N7, T5...) so findings stay unambiguous and
cross-referenceable.

## Code-level smells

| Smell | Look For | Usual Response |
| --- | --- | --- |
| Long function | mixed abstraction levels, many branches | extract named steps if touching the area |
| Mixed responsibility | unit fails the one-sentence test | split along responsibility kinds when your task touches it |
| Misplaced code | logic living in the wrong layer or module | move it to its owner, or report the mismatch |
| Junk-drawer module | growing `utils`/`helpers`/`common` | name the domain concept; relocate what you touch |
| Duplicate knowledge | same rule or constant in multiple places | centralize when behavior is changing and the duplication is true |
| Duplicate implementation | parallel versions of the same helper or file | consolidate to one; delete the orphan if provably unused |
| Primitive obsession | loose strings, numbers, maps standing in for concepts | introduce a type only when it protects a real invariant |
| Boolean flag argument | one function doing two jobs | split functions or name modes clearly |
| Repeated type-switch | same if/else or switch chain in several places | one dispatch point when idiomatic |
| Feature envy | code reaching into another module's internals | move behavior or expose a clearer API |
| Hidden temporal coupling | calls that must happen in a secret order | make state transitions explicit |
| Global mutable state | order-dependent tests, hidden inputs | inject dependencies or isolate state |
| Broad catch | failures disappear | handle, wrap, or propagate with context |
| Magic values | unexplained numbers or strings | name constants that express domain meaning |
| Buried configuration | tunable values hardcoded deep in call stacks | lift to the top level and pass down |
| Dead code | unreachable branches, unused exports, orphan files | delete what your change orphaned; report the rest |

## Structural and architectural smells

These cost more to fix and more to leave. Report them even when they are out of scope, because they
shape every later change.

| Smell | Look For | Usual Response |
| --- | --- | --- |
| Wrong-way dependency | an inner layer naming an outer one; an ORM type or framework annotation in a business rule | invert it: declare the interface on the inner side, implement it outside |
| Skipped layer | a controller wired straight to a repository or data access | route through the owning layer; check first whether the skipped layer holds the only authorization |
| Dependency cycle | components that cannot be built or released independently | invert one edge, or extract a component both depend on |
| Detail leak | rows, result sets, or request/response objects travelling inward | define a structure per crossing and copy the fields |
| Framework as architecture | top-level structure named after the stack; business objects derived from framework base classes | name packages for the domain; wrap the framework at the edge with a proxy |
| Shotgun surgery | one concept forces edits across many files | find the missing boundary |
| Unstable dependency | a widely depended-on component depending on a volatile one | extract an abstract component between them |
| Zone of pain | something stable, concrete, and volatile that much of the system depends on | put an abstraction in front of it |
| Structural test coupling | one test class per production class, mirroring methods | test behavior, not structure |
| GUI-driven business tests | business rules verified by driving the UI | test through the use case; keep the UI humble |
| Premature service split | a process or network boundary that separates behavior but shares a data record | draw the boundary inside the service instead, or collapse it |
| Accidental deduplication | one helper serving two actors, or two change rates | split it back apart; owners differ, so the code should too |

## Priority when several apply

Order the work by risk, not by how easy the fix looks:

1. Anything that can produce wrong behavior or a security hole — a skipped authorization layer, a
   broad catch hiding failures, a substitutability violation resolved with a type check.
2. Anything that blocks verification — untestable by design, structural test coupling, missing tests
   for the area you are changing.
3. Wrong-way dependencies and cycles, which make every later change more expensive.
4. Duplicated knowledge that is genuinely true duplication.
5. Readability: naming, function size, comments, magic values.

Formatting is last and usually belongs to the formatter, not to you.
