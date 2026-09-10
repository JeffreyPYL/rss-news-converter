## Context

Greenfield: no application code exists in this repo yet, only OpenSpec planning and the tooling conventions in `CLAUDE.md` and the `python-testing` skill. Three empirical findings from the exploration phase drive the shape of this design (see proposal.md for the "why"):

- Full article text for BBC, CBC, and Globe and Mail is retrievable via a plain, unauthenticated HTTP fetch — confirmed against live articles from all three, including a paywalled Globe and Mail piece. No login, session capture, or browser automation is needed for extraction.
- Comment sections on these outlets are inconsistently enabled (CBC disables them per-article; Globe and Mail restricts them to a narrow story allow-list; BBC has largely discontinued them) and, when present, only render via client-side JavaScript with no accessible read API — confirmed via live headless-browser network inspection. Comments are out of scope for this reason (proposal.md).
- No LLM API key is available — only a Claude Code subscription — so any generative step must run as a Claude Code agent turn, not a direct API call.

## Goals / Non-Goals

**Goals:**
- A single script-based pipeline (fetch → extract → group → render → deliver) that runs identically whether triggered on-demand or on schedule.
- Swappable adapters exactly where a second implementation already exists: extraction engine, feed sources, delivery targets.
- No dependency on a live browser session or stored login credentials anywhere in the pipeline.

**Non-Goals:**
- Comment/discussion extraction (dropped — see Context above).
- Any topic, outlet, or delivery target beyond what's listed in proposal.md's "What Changes".
- General-purpose RSS reader features (marking read, search, archiving) — this produces one digest per run, nothing more.

## Decisions

### Pipeline is a deterministic script, not an agent loop
The fetch/extract/group/render/delivery stages are ordinary Python, invoked by a Claude Code command or a scheduled routine — not an agent reasoning through tool calls each run. Rationale: this is repeatable ETL work; a script is cheaper, faster, and testable in the way `python-testing` expects (functional happy-path tests over a real pipeline). The one deliberate exception is synthesis (below), which genuinely needs a Claude Code agent turn.
**Alternative considered**: fully agent-orchestrated runs using WebFetch/MCP tools for every step. Rejected — it can't run unattended at 7am against a dependable, testable contract, and pytest-httpx-style testing wouldn't apply to it.

### Extraction: plain fetch, Trafilatura default, Defuddle swappable
Both extractors were run against live BBC/CBC/Globe and Mail articles during exploration; Trafilatura's output needed no post-processing (no stray UI text, no leftover iframe tags), while Defuddle's did. Both get a `Protocol`-typed port in `application/ports.py` and an adapter under `infrastructure/extraction/`, since both are real, tested implementations — not a speculative interface.
**Alternative considered**: browser-rendered extraction (for consistency with a possible future comments feature). Rejected — unnecessary complexity for content that a plain fetch already reaches.

### Story grouping happens before topic assignment
Grouping (same story, multiple outlets) must run before topic assignment, because a story's topic is decided once for the whole group, not per source article — otherwise the same story could be assigned to different topics depending on which outlet's copy is examined first. Topic assignment then applies the narrow-to-broad ranking from `story-digest`'s spec to the group as a unit.

### Synthesis: on-demand path decided now, scheduled path deferred
On-demand: the local Claude Code command's own agent turn writes the synthesis inline after the script hands back grouped stories — this is decided and being built now. Scheduled: **deferred**. The Task 2.1 spike found that a Claude Code "scheduled routine" is a cloud-sandboxed session with no access to the local filesystem — it cannot write to the local Obsidian vault, cannot share local run-state with the on-demand path, and needs a git remote this project doesn't have. That finding invalidates the original plan to route scheduled synthesis through a cloud routine; see Open Questions for the deferred mechanism decision (most likely a local `launchd` job invoking `claude -p` rather than a cloud routine, but not decided).
**Alternative considered**: a raw Anthropic API call from the script. Rejected — no API key is available; only a Claude Code subscription. This rejection holds regardless of how the scheduled trigger ends up invoked.

### Delivery targets are independent and both best-effort
Obsidian and email/Kindle delivery are separate adapters behind a `DigestDelivery`-shaped port, run independently so one failing doesn't block the other (per `digest-delivery`'s failure-visibility requirement).

## Risks / Trade-offs

- **[Risk] Extraction depends on outlets not hardening their paywalls against plain fetches.** → Mitigation: `article-extraction`'s graceful-failure requirement already covers this — a future paywall hardening degrades individual articles to teaser+link, not a pipeline failure.
- **[Risk, confirmed] A Claude Code "scheduled routine" cannot run this pipeline as designed.** The Task 2.1 spike confirmed routines are cloud-sandboxed with no local filesystem access (breaks Obsidian delivery and shared run-state) and require a git remote (this project has none). → Mitigation: the on-demand local command is being built now regardless; the scheduled-trigger mechanism is deferred (see Open Questions) rather than guessed at.
- **[Risk] RSS feed structures/URLs (especially CBC and Globe and Mail's per-topic feeds) can change without notice.** → Mitigation: per-source failure isolation (`feed-ingestion`) means a broken feed URL degrades that topic's coverage rather than the whole run.
- **[Trade-off] Trafilatura and Defuddle disagree slightly on what counts as "the article" (e.g., pull-quotes, captions).** → Accepted: the extractor is swappable, not required to be pixel-identical between implementations.

## Open Questions

- Exact EPUB-writing library (e.g., `ebooklib` vs. hand-rolled OPF/XHTML) — doesn't affect specs or approach, pick during task implementation.
- Exact synthesis prompt wording for the cross-outlet blurb — a content-quality detail to iterate on after the pipeline works, not a structural decision.
- **Deferred, not safely skippable**: the scheduled-trigger invocation mechanism (`digest-triggers`'s "Scheduled trigger" requirement). Confirmed a Claude Code cloud routine cannot do this (see Risks). Most likely direction is a local `launchd` job invoking the same script directly, with `claude -p` for the scheduled synthesis step — but this is undecided and explicitly deferred per user direction: build and ship the on-demand local command first, design the scheduled path afterward, likely as a follow-up change once the on-demand pipeline is proven. Tasks 9.3 and 10.2 are marked deferred in tasks.md pending this decision.
