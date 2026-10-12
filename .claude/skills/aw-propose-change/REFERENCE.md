# aw-propose-change: formats and rubric

## OpenSpec CLI

```bash
openspec new "<change-name>"                      # scaffold openspec/changes/<name>/
openspec status --change "<name>" --json          # artifact order and applyRequires
openspec instructions <artifact-id> --change "<name>" --json
openspec validate "<name>" --strict               # blocker gate
openspec list                                     # avoid name clashes
```

Instruction `context` / `rules` blocks constrain you. Never copy them into an artifact.

## Public API section (in proposal.md or design.md)

```markdown
## Public API
- crate `billing`: + `pub fn refund(&self, id: InvoiceId) -> Result<Refund, RefundError>`
- crate `billing`: ~ `Invoice::total` now returns `Money` (was `u64`)
- none in other crates
```

`pub` inside a crate that no other crate uses still counts only if re-exported from the crate root. Items that stay `pub(crate)` or `pub(super)` are not listed.

## Architecture opportunities (ranked: importance x urgency)

Investigate every opportunity, ponytail-filter, present survivors:

```
| # | Opportunity | Files | Importance | Urgency | Reason | Benefit | Cost if left |
```

- Importance: testability, locality, leverage, rule conformance.
- Urgency: how much this proposal is blocked or worsened by leaving it.
- Reason must pass the deletion test: it concentrates complexity, not just moves it.
- Cost if left is concrete future pain.

Then grill the user's picks. Fold small and coupled ones in; large ones become their own proposals.

## Split plan

```
Proposals:
- P1 <name> - <scope>   (independent)
- P2 <name> - <scope>   (depends on P1)
Execution:
- Parallel (one worktree each): P1, P3
- Stacked: P2 on P1
```

Default to independent PRs off `main`. Stack only for a real dependency. Plan only: create nothing.

## Rubric

| Check | Bar | Blocker? |
|---|---|---|
| OpenSpec | `validate --strict` passes; each requirement has a `#### Scenario:` and a `tasks.md` entry | yes |
| TDD seams | named, agreed, highest point; unit vs integration placement stated; behavior-lock plan (mutants) | yes if unagreed |
| Rules | no MUST in `rules/` violated | yes |
| ADRs | no contradiction with `docs/adr/` | yes |
| Boundaries | each new file has crate, layer, allowed users, allowed deps | yes |
| Public API | section present and complete | yes |
| Ponytail | no speculative scope | warning |
| Split | dependencies correct, "independent" verified | warning |
| Arch ranks | reason, benefit, cost, defensible rank | warning |

Loop review, fix, re-review until zero blockers.

## Hand-off summary

Change names and paths, split plan, ranked opportunities (folded vs deferred), issue numbers (or skipped), next command (`/aw-implement`, then `/aw-ship-review`).
