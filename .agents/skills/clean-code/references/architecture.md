# Architecture

Clean code is about the lines inside a unit. Architecture is about the lines *between* units:
where they run, and which way the dependencies cross them. Read this file when a task involves
placement across layers, a new dependency, a boundary, a framework or database decision, or any
question of the form "where should this live and what may it know about?"

The whole subject reduces to one rule and one question.

**The Dependency Rule: source code dependencies must point only inward, toward higher-level
policies.** Nothing in an inner circle may know anything about an outer circle. In particular the
*name* of anything declared in an outer circle must not appear in inner-circle code — no class,
function, variable, annotation, or data format.

**The question to ask before every dependency: which direction does this line cross, and why?**

## Level, policy, and detail

**Level is distance from the inputs and outputs.** The farther a policy sits from I/O, the higher
its level. This is the definition that decides placement, and it is not the same as call order: a
function that calls `readChar` and `writeChar` is *higher* level than they are, even though it is
the caller.

- **Policy** is the business rules: the reason the software exists.
- **Detail** is everything that helps policy talk to the world: the database, the web, the UI, the
  framework, the delivery mechanism, the device, the protocol.

Group policies that change for the same reasons at the same times into the same level. Different
reasons or different rates mean different levels, and therefore different components.

Design so that **low-level components depend on high-level ones**, never the reverse. The
component dependency graph is a graph of compile-time dependencies (`import`, `using`, `require`)
and it must be acyclic.

### The two kinds of business rule

- **Critical Business Rules** and **Critical Business Data** would exist even if the business ran
  on paper with no software at all. Bind them together into an **Entity**: a module holding a
  small set of critical rules operating on critical data. An Entity is pure business and nothing
  else. It needs no object-oriented language — only that the data and its rules live in one
  separate module.
- A **use case** describes how an automated system is used: input, output, processing steps. It
  holds *application-specific* rules and orchestrates the Entities.

The dependency follows: **use cases depend on Entities; Entities do not depend on use cases.** Use
cases are closer to I/O, so they are lower level.

Practical test: if the rule is still true with pen and paper, it belongs in an Entity. If it exists
only because the work was automated, it belongs in a use case. From inside a use case it must be
impossible to tell whether the delivery mechanism is a web app, a console, a desktop client, or a
service.

## The circles

Outermost to innermost. The count is schematic — add circles freely — but the Dependency Rule
always applies.

1. **Frameworks and drivers** — the database, the web framework, the device, the tools. All the
   details go here, plus glue code. The web is a detail. The database is a detail.
2. **Interface adapters** — code that converts between the form convenient to the use cases and
   the form convenient to some external agency. Controllers, presenters, views, gateways, and
   mappers live here. **All SQL is confined to this layer**; nothing further in knows a database
   exists.
3. **Use cases** — application-specific rules, orchestrating the flow to and from Entities.
4. **Entities** — enterprise-wide critical business rules. No change to any single application
   should force a change here.

Outer circles are mechanisms; inner circles are policies. This shape is the common core of
Hexagonal / Ports and Adapters, DCI, and BCE — the names differ, the rule does not.

### Crossing a boundary

At run time a boundary crossing is just a function on one side calling a function on the other and
passing data. The design work is entirely in the *source* dependencies.

Control flow and source dependency point the same way on an inbound call, and *opposite* ways on
an outbound one. A controller calls into a use case, and the use case must deliver a result
outward to a presenter — but the use case may not name the presenter. Resolve this with dynamic
polymorphism: the use case calls an interface it owns (an **output port**) and the presenter in the
outer circle implements it. The dependency now opposes the flow of control, which is exactly what
Dependency Inversion means.

**Which data may cross:** simple, isolated structures — a struct, a plain DTO, function arguments,
a basic map. Always in the shape most convenient for the *inner* circle.

**What may never cross inward:** an Entity object, a database row, an ORM row type, a result set, a
framework request or response object. When fields happen to overlap, define a separate structure
per crossing and copy the fields anyway; sharing the type is a Single Responsibility violation that
returns later as tramp data and special-case conditionals.

### The cost of each boundary

Chattiness must match the boundary's cost, because a conversation shaped for one boundary becomes a
performance failure when the same boundary becomes another kind.

| Boundary | Mechanism | Crossing cost | Chattiness |
| --- | --- | --- | --- |
| Same address space (monolith) | function call | very cheap | can be very chatty |
| Deployment component (jar, DLL, shared library, gem) | function call plus one load-time cost | very cheap | can still be chatty |
| Local process | OS calls, marshaling, context switches | moderately expensive | limit it carefully |
| Service | network | very slow: tens of milliseconds to seconds | avoid chatting |

Threads are not boundaries and not units of deployment — they are scheduling.

### Full, partial, and no boundary

A full boundary costs reciprocal interfaces, input and output structures, and the dependency
management to keep them apart. It buys independent compilability and deployability. When the case
for one is "not yet, but I might", use a partial boundary and know its specific weakness:

- **Skip the last step** — build the separated components but deploy them as one. Cheapest to
  reverse; the separation quietly erodes as dependencies creep back across.
- **One-dimensional boundary** (a Strategy interface, no reciprocal interface) — nothing but
  discipline stops someone adding a backchannel.
- **Facade** — sacrifices dependency inversion entirely: the client gains a transitive dependency
  on everything behind the facade and recompiles when any of it changes.

Prefer Strategy over Facade when the client must not recompile. Whichever you pick, add
compile-time or automated enforcement — a partial boundary does not maintain itself.

Implement a boundary at the inflection point where the cost of building it drops below the cost of
going without it. Declare each boundary interface in the component that *uses* it: the API is owned
by the user, not the implementer.

## SOLID, as dependency rules

These are not style advice. Each one prevents a specific structural failure.

**SRP — Single Responsibility Principle.** *A module should be responsible to one, and only one,
actor.* An actor is the group of people who can demand a change. This is the most misread
principle in the set: "a module should do one thing" is a real and useful rule for functions, but
it is **not** the SRP. The SRP says to separate code that different actors depend on.

- Before placing a function, ask which actor can demand that it change. Never co-locate code
  answering to different actors.
- Do not deduplicate across an actor boundary. Two identical-looking calculations owned by
  different actors must stay separate; merging them is how one department's change silently
  corrupts another's numbers.
- Read repeated merge conflicts in one file as an SRP violation, not a process problem.

**OCP — Open-Closed Principle.** *A software artifact should be open for extension but closed for
modification.* Behavior should be extendable by adding code, not by editing existing code.

- The directional rule: **if A must be protected from changes in B, then B depends on A.** Arrows
  point toward what you are protecting.
- Never let business rules reference a presenter, view, database, or UI type. Invert with an
  interface owned by the policy side.
- Keep each boundary crossed in one direction only, and keep the interface narrow: a wide
  interface leaks internals as transitive dependencies on things the caller never uses.

**LSP — Liskov Substitution Principle.** A subtype must be usable anywhere the base type is,
without the caller's behavior changing.

- The proof of a violation is a call site that must know which implementation it has. A type check
  or a vendor-name special case at a call site *is* the violation.
- Applies to every substitutable boundary, not just class inheritance: REST contracts, plugin
  interfaces, duck-typed objects, sets of services behind one interface.
- One substitutability failure spreads: the workaround conditional multiplies into extra
  mechanisms, and those conditionals are a frequent source of security holes.

**ISP — Interface Segregation Principle.** Avoid depending on things you do not use. The common
reading, "keep interfaces small", is a symptom of the real rule, which is about dependency on
*unused* things: it is harmful to depend on a module containing more than you need.

- Define the narrow interface the caller actually needs rather than consuming a wide existing type.
- Before adding a dependency, look at what *it* depends on. Transitive baggage sets both the
  recompile blast radius and the failure blast radius: a fault in an unused feature of a
  dependency can still take you down.

**DIP — Dependency Inversion Principle.** The most flexible systems are those whose source
dependencies refer only to abstractions, never to concretions.

- The test is **volatility, not abstractness**. Depending on the standard library's string type is
  fine; it is stable. Depending on a volatile concrete class of your own is not.
- The four practices: do not refer to a volatile concrete class; do not derive from one
  (inheritance is the strongest and most rigid source relationship); do not override a concrete
  function (you inherit its dependencies rather than escaping them); never mention the name of
  anything concrete and volatile.
- Creating an object is itself a concrete dependency, so policy code must not `new` a volatile
  class. Use an abstract factory.
- Violations cannot be removed entirely — gather them into a small number of concrete components,
  usually `main`.

## Component principles

A component is a unit of deployment: the smallest thing you can deploy independently. Keep that
independence even inside a single executable — losing it turns a partitioned system into a monolith
that cannot be split.

### Cohesion: which classes belong together

- **REP — Reuse/Release Equivalence Principle.** *The granule of reuse is the granule of release.*
  Anything you expect others to reuse must be tracked and released as a unit.
- **CCP — Common Closure Principle.** *Gather into components those classes that change for the
  same reasons and at the same times; separate those that change at different times and for
  different reasons.* This is the SRP restated for components.
- **CRP — Common Reuse Principle.** *Don't force users of a component to depend on things they
  don't need.* This is ISP restated for components.

These three pull against each other. REP and CCP are inclusive — they make components larger. CRP
is exclusive — it makes them smaller. Over-weighting REP and CRP means one simple change touches
too many components; over-weighting CCP and REP means too many needless releases. Early in a
project, favour CCP: develop-ability matters more than reuse. Shift weight toward REP only once
real external consumers exist.

### Coupling: which components may depend on which

- **ADP — Acyclic Dependencies Principle.** *Allow no cycles in the component dependency graph.* A
  cycle fuses the components into a single release unit, makes build problems grow geometrically,
  and can leave no valid build order at all. Break a cycle by applying DIP, or by extracting a new
  component that both existing ones depend on.
- **SDP — Stable Dependencies Principle.** *Depend in the direction of stability.* Stability here
  is not frequency of change; it is the work required to change something. A component many others
  depend on is hard to move.
- **SAP — Stable Abstractions Principle.** *A component should be as abstract as it is stable.* A
  stable component must be abstract enough to be extended without modification, which is OCP again.

SDP and SAP together are the DIP for components: depend toward stability, and stability implies
abstraction, so dependencies run toward abstraction. DIP is binary per class; these two allow
degrees.

### The metrics

Useful when you need evidence rather than opinion about a component graph.

- **Fan-in** = classes outside the component that depend on classes inside it.
- **Fan-out** = classes inside the component that depend on classes outside it.
- **Instability `I = Fan-out / (Fan-in + Fan-out)`**, ranging 0 to 1. `I = 0` is maximally stable
  (depended upon, depending on nothing): responsible and independent. `I = 1` is maximally unstable:
  irresponsible and dependent.
- **SDP in metric form:** `I` should *decrease* in the direction of dependency. Before adding a
  dependency from A to B, check that `I(A) > I(B)`. A stable component depending on a deliberately
  flexible one destroys the flexible one's changeability without editing a line of it.
- **Abstractness `A = Na / Nc`**, where `Nc` is the number of classes in the component and `Na` the
  number of abstract classes and interfaces. `A = 0` means nothing abstract; `A = 1` means nothing
  but abstractions.
- **The Main Sequence** is the line from `(I=1, A=0)` to `(I=0, A=1)`. The two endpoints are the
  most desirable positions: stable and abstract, or unstable and concrete.
- **Distance `D = |A + I - 1|`**, ranging 0 to 1. `D = 0` sits exactly on the Main Sequence.
  Investigate any component much above roughly `0.1`, or more than one standard deviation from the
  mean `D` of your own design. A metric is a measurement against an arbitrary standard, not a verdict.

**Zone of Pain** is near `(I=0, A=0)`: stable and concrete, therefore rigid. A database schema is
the archetype — highly depended upon, extremely concrete, and volatile. Volatility is effectively a
third axis, which is why a stable concrete thing like a standard string type is harmless there.
**Zone of Uselessness** is near `(I=1, A=1)`: abstractions nobody implements or depends on.

Component structure cannot be designed top-down before code exists. It maps buildability and
maintainability, not function, so it evolves with the system. A useful convention: draw unstable
components at the top of a diagram, so every upward arrow is a visible violation.

## Keeping details out

**Screaming architecture.** The top-level structure should announce the domain, not the framework.
If the directory listing says "Rails" or "ASP.NET" rather than "billing" or "patient records", the
framework has become the architecture. Name top-level packages after the domain and its use cases.

**Frameworks are details.** Using a framework is an asymmetric commitment: you commit enormously,
the author commits nothing to you. So use it, but do not couple to it. Never derive an Entity or
use case from a framework base class — derive a proxy in an outer circle instead. Keep framework
annotations off business objects. Confine dependency-injection framework usage to `main`; inject
there, then pass dependencies onward normally. Before adopting any framework answer both questions:
how do I use it, and how do I protect myself from it?

**The database is a detail.** The *data model* is architecturally significant; the database system
is not. Never let rows, tables, result sets, or ORM row types travel beyond the data-access layer —
allowing them to circulate as objects is an architectural error. Confine SQL and knowledge of
tabular structure to the outermost utilities. Handle storage performance inside the access
mechanism, not by reshaping business rules.

**The web is a detail.** The GUI is a detail, the web is a GUI, so the web is an I/O device. The
moment-to-moment interaction with a UI is genuinely hard to abstract, but the *use case* boundary is
not: gather complete input, process it, return output data, all in plain structures. Keep HTTP,
session, and widget concepts out of business rules.

**`main` is the ultimate detail** — the lowest-level policy, the dirtiest component, and the only
one nothing else depends on. All wiring, configuration loading, and framework binding belong there.
Treat `main` as a plugin: prefer a separate `main` per environment, jurisdiction, or customer over
configuration branches inside policy code.

## Systems: construction, growth, and cross-cutting policy

**Separate constructing the system from using it.** Startup is its own concern: building the object
graph, reading configuration, choosing implementations. Code that does real work should receive what
it needs, never go and build it. The moment a business rule constructs its own dependency, it has
taken on a second job and become untestable in isolation.

- Use factories when an object must be created *during* execution rather than at startup — the
  calling policy names the factory interface, and the concrete factory lives outward.
- Use dependency injection to move construction to `main`. Inject there, then pass dependencies
  onward as ordinary arguments; do not scatter the framework's annotations through the system.
- **Lazy initialization is a construction decision leaking into use.** It hardcodes a concrete type
  at the point of use and makes the null-check path part of the business logic.

**Systems grow; they are not built whole.** Software architecture is not physical architecture — you
cannot pour the foundation once and be done, and pretending otherwise is why big up-front design
fails. A clean system starts simple and grows because its concerns stayed separated: new use cases
arrive as new components rather than as edits spread across old ones. Decide at the **last
responsible moment**, with the most information and the least commitment.

**Isolate cross-cutting concerns.** Persistence, transactions, security, logging, caching, and
metrics apply across many modules and cut against clean separation — implemented naively they end up
duplicated in every handler. Concentrate each one in a single place and apply it at a boundary:
middleware, a decorator, a proxy, an interceptor, an aspect, whatever the ecosystem provides. The
principle is what matters, not the mechanism: **one home per policy, applied at the edge, invisible
to the business rules it protects.**

**Test-drive the architecture.** If you can write a use case's tests with no database, no web server,
and no framework running, the architecture is decoupled — the test suite is the proof, not the
diagram. If you cannot, the coupling is real regardless of what the diagram claims.

**Use standards wisely, and build a language when it pays.** Adopt a standard when it demonstrably
buys interoperability or reuse, not because it is a standard — an over-engineered standard adopted for
its own sake costs more than it returns. And where a domain concept recurs constantly, a small
domain-specific language or a well-named vocabulary of helpers lets the code state intent directly
instead of restating mechanism. That is the same instinct as the testing language in `tests.md`.

## Testability is an architectural property

**The Humble Object pattern.** When behavior is hard to test, split it into two modules rather than
building a harness around it. One module is *humble*: it holds the hard-to-test behavior stripped to
its barest essence, with no decisions in it. The other holds everything testable that was stripped
out.

At every architectural boundary this pattern is somewhere nearby, because boundaries tend to fall
exactly where hard-to-test meets easy-to-test. Separating the two often *is* how you find the
boundary.

- A **view** is the humble object: it moves data onto the screen and makes no decisions. The
  **presenter** is the testable half, and it does all the work — formatting dates and currency into
  strings, deciding what is greyed out or highlighted, choosing button and field labels. Anything on
  screen that the application controls should appear in the view model as a string, a boolean, or an
  enum.
- A **database gateway** is an interface with one intention-named method per operation. The
  implementation is the humble object. Never put SQL in a use case.
- An **ORM belongs in the database layer** and forms another humble-object boundary. Objects and
  data structures are not the same thing: an object exposes behavior and hides data, a data
  structure exposes data and implies no behavior.

**Tests are a system component** and participate in the architecture like any other. They are the
outermost circle: maximally detailed, depending inward, depended on by nothing.

- The first rule of design applies to them too: do not depend on volatile things. GUIs are volatile,
  so a suite that drives business rules through the GUI is fragile by construction.
- **Structural coupling** is the most insidious form of test coupling: a test class per production
  class, a test method per production method. It makes tests fragile and production code rigid, and
  it blocks the divergence that should happen as production code grows more general while tests grow
  more specific.
- When a fragile suite makes developers refuse an otherwise correct change, that rigidity is the
  cost being paid.
- Provide a **testing API** that hides application structure from the tests and can bypass security
  and expensive resources to force testable states. Keep it, and its dangerous implementation, in a
  separately deployable component.

## Packaging: four strategies and their weaknesses

How you group code decides whether the architecture can be enforced by the compiler or only by
discipline.

| Strategy | Structure | Specific weakness |
| --- | --- | --- |
| **Package by layer** | horizontal: web / business logic / persistence | Three buckets stop scaling, the structure says nothing about the domain, and a controller can be wired straight to a repository while the dependency graph still looks clean and acyclic |
| **Package by feature** | vertical slice per feature or aggregate | Better — the structure now announces the domain — but a single public entry point per feature may be more or less restrictive than you want |
| **Ports and adapters** | domain "inside", infrastructure "outside", outside depends on inside | With one shared infrastructure tree, a controller can reach a repository directly and circumnavigate the domain entirely |
| **Package by component** | business logic *and* its persistence behind one interface per coarse-grained component; UI separate | Requires real discipline about what is public, and one assembly or module per component in some ecosystems |

**Organization versus encapsulation is the decisive point.** If every type is public, packages are
only a grouping mechanism — like folders — and all four strategies above become *syntactically
identical*, however different they look on a diagram. Nothing then prevents code anywhere from
instantiating an implementation class directly and violating the intended design.

So: never mark a type public by default. Use package-private, `internal`, or your language's
equivalent unless another package genuinely needs an inbound dependency. Give each component one
public entry point, so the compiler — not a code review — is what blocks a controller from calling
a repository.

The enforcement ladder, weakest to strongest: discipline and code review (which fails when
deadlines loom), post-compile static analysis (crude, and the feedback loop is long), and the
compiler (immediate and unarguable). Prefer the compiler whenever the language allows it.

## Decoupling modes

Three ways to separate components, in increasing cost:

1. **Source level** — control dependencies between source modules so a change does not force others
   to recompile. All components share one address space and communicate by function calls. This is
   what people usually call a monolith.
2. **Deployment level** — control dependencies between independently deployable units: jars, DLLs,
   shared libraries. Many still share an address space.
3. **Service level** — reduce dependencies to data structures exchanged over the network, so each
   unit is independent of the others' source and binaries.

The best mode is hard to know early and changes as a system matures, so **push the decoupling to the
point where a service could be formed if it became necessary, then leave the components in the same
address space as long as possible.** Keep the progression reversible in both directions. Never write
code that depends on the current mode — no hard-coded network hop, no assumption of a shared address
space.

Service boundaries are not architectural boundaries by themselves. Services separated only by
behavior are expensive function calls: they remain strongly coupled through the data they share, and
adding a field to a shared record forces every service touching it to change and to agree on its
meaning. A service interface is no more rigorous than a function interface. **Architectural
boundaries run *through* services, dividing them into components** — not between them. Test a
decomposition by counting how many units a cross-cutting feature forces you to change; if the answer
is "all of them", the decomposition is functional, not architectural.

Micro-services are also not automatically finer-grained decoupling, and they cost development time —
which, unlike memory and cycles, is not cheap.

## Duplication: resist the reflex

Eliminating duplication is right only when the duplication is real.

- **True duplication**: every change to one instance requires the same change to every copy.
- **False (accidental) duplication**: the copies change at different rates, for different reasons.

Two shapes that look identical today and diverge tomorrow are not duplicates. A database record
shaped like a screen view is almost certainly accidental duplication — build the separate view model.
Similar-looking screens across different use cases usually are too. Unifying accidental duplication
is much harder to undo than leaving it alone, and it is one of the most common ways an agent damages
a codebase while believing it is cleaning it.

## Architecture serves the developer

The goal of architecture is to **minimize the human effort required to build and maintain the
system** — so the strategy is to leave as many options open as possible, for as long as possible. A
good architect maximizes the number of decisions *not* made.

Architecture has almost no bearing on whether the system works right now; its value is entirely in
what happens next. Behavior is urgent but not always important; structure is important but never
urgent, which is why it loses arguments it should win. The tell of a structural defect is a
mismatch between *scope* and *shape*: the difficulty of a change should be proportional to its
scope, never to its shape. When a small requirement forces a large diff, that is an architecture
defect, and it should be named as one rather than absorbed silently.

- Never justify a shortcut with "we will clean it up later"; the pressure that created it never
  abates.
- Never propose a rewrite as the remedy for a mess. The team that made the mess rebuilds it.
- Treat rising cost per comparable change as the primary signal of decay.
- Never treat "it satisfies the requirements" as done.

## Related files

- `architecture-map.md` — per-chapter map from architectural topics to the decisions they govern.
- `principles.md` — the code-level principles: naming, functions, errors, tests, concurrency.
- `chapter-map.md` — code-level chapter map and the full code-smell catalogue with IDs.
- `new-project.md` — designing a structure from scratch.
- `project-refactor.md` — changing an existing structure safely.
