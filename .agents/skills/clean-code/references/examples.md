# Worked Examples

Concrete before-and-after cases, and two output templates. These are illustrative, not language
mandates — the lesson transfers, the syntax does not.

## Do not abstract for requirements that do not exist

**Request: apply a 10 percent invoice discount.**

Too much — a strategy hierarchy with parameters for rules nobody asked for:

```python
class DiscountStrategy:
    def calculate(self, invoice):
        raise NotImplementedError

class PercentageDiscountStrategy(DiscountStrategy):
    def __init__(self, percent, max_amount=None, min_total=None):
        self.percent = percent
        self.max_amount = max_amount
        self.min_total = min_total

    def calculate(self, invoice):
        # branches for requirements that do not exist yet
        ...
```

Enough for the request:

```python
def discount_amount(invoice_total: Decimal) -> Decimal:
    return invoice_total * Decimal("0.10")
```

Add the strategy when there is a second real discount rule. Note the `Decimal`: money is never a
float.

## Let names carry the intent, then delete the comment

Weak — the comment exists because the code is unreadable:

```typescript
// Check if the user can access the report
if (u.a && r.s !== 'x') {
  return true
}
```

Cleaner:

```typescript
const hasActiveSubscription = user.subscriptionActive
const reportIsNotArchived = report.status !== 'archived'

return hasActiveSubscription && reportIsNotArchived
```

The comment became unnecessary. Explanatory variables named the two conditions, which is what the
comment was compensating for.

## Preserve the cause when wrapping an error

Weak — the error propagates with no indication of what failed:

```go
payload, err := client.Fetch(ctx, id)
if err != nil {
    return nil, err
}
```

Cleaner:

```go
payload, err := client.Fetch(ctx, id)
if err != nil {
    return nil, fmt.Errorf("fetch customer %s: %w", id, err)
}
```

`%w` keeps the original error inspectable, and the message says which customer failed. Context added,
nothing hidden.

## Make the boundary explicit in SQL

Weak — implicit join, `SELECT *`, and a value pasted into the statement:

```sql
SELECT *
FROM orders o, customers c
WHERE o.customer_id = c.id
AND c.email = 'user input here';
```

Cleaner:

```sql
SELECT
  o.id,
  o.created_at,
  o.total_amount
FROM orders AS o
JOIN customers AS c ON c.id = o.customer_id
WHERE c.email = :email;
```

Named columns survive a schema change, the join is explicit, and parameter binding belongs to the
client — which is also what closes the injection hole.

## Split mixed responsibilities — when the task touches them

Weak — one function parses transport data, validates, persists, sends mail, logs, and renders:

```python
def register_user(raw):
    data = json.loads(raw)
    if "@" not in data["email"]:
        return {"error": "bad email"}
    user = db.insert("users", data)
    smtp.send(data["email"], WELCOME_TEMPLATE)
    log.info("registered %s", data["email"])
    return {"id": user.id, "html": render("welcome.html", user)}
```

Testing it needs a database, an SMTP server, and a template engine — the test-pain check, telling you
it mixes concerns.

Cleaner shape: `register_user` becomes an orchestrator sequencing `parse_registration(raw)`,
`validate_registration(data)`, `create_user(data)` and `send_welcome(user)`. Each is testable alone
and lives in the layer the project uses for that concern. Rendering stays in the view layer that
called it, and the orchestrator holds no business rules of its own.

**Do not perform this split as a drive-by during an unrelated fix.** Do it when the task touches this
function; otherwise record it as a finding.

## Template: reporting completion honestly

Weak:

> This should work now.

Clean:

> I ran `npm test -- email-validator` and the empty-email regression test passes. I did not run the
> full suite.

The difference is evidence and a stated gap. The second sentence is the one that matters.

## Template: a campaign contract

When cleanup itself is the task, agree this before editing anything (see `project-refactor.md`):

```text
Proposed contract: structural depth, src/ only, behavior-preserving, one commit per batch.
Baseline: 214/214 tests pass; lint clean; build green (recorded verbatim).
Plan: 1) delete dead exports  2) rename ambiguous managers to domain names
      3) split mixed-responsibility services  4) normalize error wrapping.
Ledger: .clean/ledger.md tracks batches, findings, and deferred bugs.
```

Each batch is verified against the baseline and committed separately. A rounding bug found during
batch 3 goes into the ledger for the user — never silently fixed inside a rename commit.

## Template: review findings

A review that only mentions naming and function length is too shallow. Scan the map and group by
concern, citing smell IDs (see `chapter-map.md`):

```text
Findings:
- Boundary: vendor errors are passed through without a local contract.
- Tests (T6): retry and timeout paths are untested near a recent production bug.
- Concurrency: job cancellation can race with queue acknowledgement.
- Functions (G30): `processBatch` validates, transforms, persists, retries, and emits metrics.

No findings in comments or formatting after formatter output.
```

Findings first, each with a location and a consequence. No invented rewrites.
