# Architecture

<!--
Copy this file to .clean/architecture.md in your project and fill it in.

It has two jobs. The prose explains the design to a human. The fenced
`clean-architecture` block below is machine-readable: scripts/check_boundaries.py
reads it and fails the build when a source dependency points the wrong way.

Declare layers INNERMOST FIRST. The default rule is the Dependency Rule: a layer may
depend on itself and on any layer declared before it, and on nothing declared after it.
Add `allow` or `deny` lines only for boundaries you intend.
-->

## What this system is for

<One paragraph. The domain, not the technology. A newcomer should be able to tell what the software
does without knowing what it is built with.>

## Layers

<For each layer: what belongs in it, and what must never appear in it.>

- **domain** — Critical business rules and data: the things that would be true even if this work were
  done on paper. Depends on nothing. No framework types, no ORM base classes, no HTTP objects, no SQL.
- **application** — Use cases. Orchestrates the domain to satisfy one application-specific job. Owns
  the interfaces it needs from the outside world (repository ports, gateway ports).
- **adapter** — Controllers, presenters, views, serializers, CLI entry points. Converts between the
  shape convenient to the use cases and the shape convenient to the outside.
- **infrastructure** — Database access, HTTP clients, message queues, file systems, framework
  wiring. Implements the ports declared inward. All SQL lives here.

```clean-architecture
layer domain         = src/domain/**
layer application    = src/application/**
layer adapter        = src/adapter/**
layer infrastructure = src/infrastructure/**

# Optional overrides. The default is inward-only, so most projects need none.
# allow infrastructure -> domain
# deny  adapter -> infrastructure

# Optional: if your import names do not match the directory names, list the tokens
# that identify each layer inside an import path or namespace.
# namespace domain = domain, entities, model
```

## Dependency rules in words

- Source dependencies point inward only. Nothing in an inner layer may name anything in an outer one
  — not a class, a function, a variable, an annotation, or a data format.
- When an inner layer needs something from outside, it declares the interface and an outer layer
  implements it.
- Data crossing a boundary is a simple structure shaped for the inner side. Entities, database rows,
  ORM types, and framework request or response objects never travel inward.
- The component graph has no cycles.

## Decoupling mode

<Which mode this project is in, and what would justify moving: source level (one address space,
function calls), deployment level (separately deployable units), or service level (network). Default
to source level and keep the move reversible.>

## Deliberate exceptions

<Any place the rules above are knowingly broken, with the reason and the condition for fixing it. An
undocumented exception is a defect; a documented one is a decision.>

## How to check

```sh
python <skill>/scripts/check_boundaries.py          # dependency direction
python <skill>/scripts/scan_repo.py                 # measurable smells
```

Both are optional accelerators. The rules above hold whether or not anything runs them.
