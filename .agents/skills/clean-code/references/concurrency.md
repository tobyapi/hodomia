# Concurrency

Concurrency decouples *what* gets done from *when* it gets done, which improves throughput and
structure — and introduces a class of defect that ordinary testing does not catch. Read this before
writing or changing anything that runs in more than one thread, task, process, or request handler
that shares state.

The defining property: a concurrency bug is not reliably reproducible. A system can pass every test
for a year and still be wrong.

## Myths worth naming

- **"Concurrency always improves performance."** Only when there is genuine wait time to reclaim.
- **"Design does not change."** Decoupling what from when changes the design substantially.
- **"The container or framework handles it."** You still have to know what it guarantees, what it
  does not, and what your own state does under concurrent access.
- **"Concurrency is not much extra work."** It adds a second correctness problem on top of the first,
  plus overhead, plus non-deterministic failure.

## Defense principles

**Apply the Single Responsibility Principle.** Concurrency policy is its own reason to change, so it
gets its own modules. Keep it out of business logic — code mixing threading with domain rules cannot
be reasoned about or tested as either one.

**Limit the scope of shared data.** Every location where shared mutable data is accessed is a place
the bug can be. Take copies of the data where you can, use immutable values by default, and confine
whatever must mutate to as few named places as possible. Race conditions, deadlocks, and
concurrent-update defects all trace back to mutable variables — there are no deadlocks without
mutable locks.

**Keep threads as independent as possible.** A task that shares nothing cannot race. Prefer designs
where each unit of work owns its own data and communicates results rather than sharing state.

**Know your library.** Use the thread-safe collections, executors, and non-blocking primitives your
platform provides rather than hand-rolling locks. Know which classes are explicitly *not*
thread-safe, and know that composing two thread-safe calls does not give you a thread-safe operation.

## The named execution models

Recognize which one you are in — each has a known failure and a known solution.

**Producer-Consumer.** Producers put work in a bounded queue; consumers take it. The queue is the
shared resource, and both sides must signal the other. The failures are lost signals (a consumer
waits forever for work that arrived) and a full queue silently blocking producers. Backpressure is
part of the design, not an afterthought.

**Readers-Writers.** Many readers, occasional writers, one shared resource. The failures are stale
reads if writers are starved, and starvation of writers if readers are unlimited — plus throughput
collapse if you serialize everything to avoid both. The trade is deliberate: decide which side may
starve and bound it.

**Dining Philosophers.** Several processes competing for several shared resources, each needing more
than one at a time. This is the shape of most real lock contention, and its failures are deadlock,
livelock, and starvation. The solution is not more locking but a resource-ordering discipline, so no
cycle of waiting can form.

Most concurrency problems you meet are a variant of one of these three.

## Locking discipline

- **Beware dependencies between synchronized methods.** More than one synchronized method on the
  same shared object invites subtle failure: each call is atomic, the sequence is not. Where a
  sequence must be atomic, provide one method that does the whole sequence — client-side locking and
  adapted server-side locking both work, but they must be chosen deliberately, not stumbled into.
- **Keep synchronized sections small.** Locks are expensive and every critical section is a
  bottleneck and a deadlock opportunity. Guard the smallest region that preserves the invariant — but
  never split one invariant across two critical sections to make them smaller.
- **Writing correct shutdown code is hard.** Signalled-and-waiting is the usual deadlock: workers
  waiting for work that will never arrive, a parent waiting for children that are blocked. Design
  shutdown early, and test it — this is where "it hangs occasionally in production" comes from.

## The four conditions for deadlock

Deadlock requires all four simultaneously, so breaking any one prevents it:

1. **Mutual exclusion** — a resource cannot be shared.
2. **Hold and wait** — a holder waits while acquiring another resource.
3. **No preemption** — a resource cannot be taken from its holder.
4. **Circular wait** — a cycle of processes each waiting on the next.

In practice you break hold-and-wait (acquire everything at once, release everything on failure) or
circular wait (a global ordering on lock acquisition). Breaking mutual exclusion means removing the
sharing; breaking no-preemption means timeouts and release, which is often the pragmatic answer.

## Testing threaded code — seven distinct tactics

A single unit test proves nothing here. These are separate tactics, and the last is the one that
actually finds races:

1. **Treat every spurious failure as a candidate threading defect.** Never re-run until green and
   move on. "Flaky test" is a diagnosis nobody made; intermittent failure is a defect report.
2. **Get the non-threaded code working first.** Do not debug two problems at once. Verify the logic
   single-threaded, then add concurrency.
3. **Make the threaded code pluggable and tunable.** Thread count, queue sizes, and timing should be
   configurable, so the same code can run in one thread for logic tests and many for stress tests.
4. **Run with more threads than processors.** Task switching happens at the points where state is
   inconsistent; oversubscription forces more of those switches.
5. **Run on different platforms.** Thread scheduling differs by OS and runtime. Code that passes only
   on your machine has not been tested.
6. **Instrument the code to force failures.** Insert jitter deliberately — sleeps, yields, or
   priority changes at points where a switch would be damaging — so rare interleavings become common.
   Do it either by hand-placed hooks or by an automated harness that randomizes them.
7. **Run the suite many times, and keep the failures.** With jitter in place, a run count of hundreds
   turns a one-in-a-million interleaving into a reproducible test.

## Throughput is a calculation, not a hope

Adding threads improves throughput only in proportion to the wait time you reclaim. Before adding
concurrency, know what fraction of the work is I/O wait versus processing — if it is nearly all
processing, more threads add contention and overhead and make things slower. When you do add it,
measure rather than assume; a bottleneck that moved is not a bottleneck removed.

## Related

- `principles.md` — the summary rules for concurrency and state.
- `tests.md` — general test discipline; this file supersedes it for threaded code.
- `architecture.md` — why immutability and segregated mutability are architectural choices, and the
  decoupling modes that decide what shares an address space.
- `chapter-map.md` — the concurrency chapter checklist and the concurrency appendix.
