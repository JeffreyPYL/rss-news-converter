---
name: python-testing
description: Write or review a Python test in this repo, mock an httpx call, run mutation testing, or check a CRAP score. Use when writing new tests, touching existing tests, or asked to check test/code quality.
---

Tests in this repo are functional-first: each use case gets one happy-path test exercising the real pipeline (fetch → extract → group → render → deliver) end to end, with only the network boundary mocked. Unit tests for `domain/` logic (pure, no I/O) are separate and don't need mocking at all.

## Mocking: fixtures, never patch

Every outbound call goes through `httpx`, so `pytest-httpx`'s `httpx_mock` fixture is the only mocking mechanism for HTTP. Never use `unittest.mock.patch` (decorator or context-manager form) or inline `Mock()`/`MagicMock()` construction inside a test body — if a test needs a double, it takes a named fixture from `conftest.py`, even for a one-off response.

```python
# conftest.py
import pytest

@pytest.fixture
def bbc_rss_response(httpx_mock):
    httpx_mock.add_response(url="https://feeds.bbci.co.uk/news/world/rss.xml", text=SAMPLE_BBC_RSS)

# test_digest.py
def test_build_digest_happy_path(bbc_rss_response, httpx_mock):
    ...
```

Reach for a new fixture even when only one test uses it today — the rule is about *how* a double is constructed (named, in `conftest.py`), not about reuse count.

## Mocking a third-party SDK: fake the SDK, not its transport

When a dependency's official SDK (the `dropbox` package, `google-api-python-client`, etc.) is used instead of calling a plain REST API over `httpx`, don't try to intercept whatever HTTP library that SDK uses internally — we don't maintain it, and its transport is the SDK's business, not ours (worse, it may not even be `httpx`, so `httpx_mock` wouldn't see it regardless). Treat the SDK the same way `ProcessRunner` (`subprocess.run`), `ExtractFn` (`trafilatura.extract`), and `SmtpSender` (`smtplib`) are already treated in this codebase: inject the SDK's client object — or a narrow `Protocol` capturing only the handful of calls actually used — as a constructor parameter, defaulting to the real client. A test injects a hand-written fake implementing that same interface, exactly like every other fixture-based double here.

```python
class DropboxClient(Protocol):
    def files_upload(self, content: bytes, path: str) -> object: ...

class DropboxApiDelivery:
    def __init__(self, client: DropboxClient, folder_path: str) -> None:
        self._client = client
        self._folder_path = folder_path
```

This tests that *our* glue code calls the SDK correctly and turns its results/exceptions into our own types (e.g. `DeliveryError`) — not that the SDK's HTTP layer works, which is the SDK's own test suite's job, not ours.

## Mutation testing

Run `mutmut run` (wired as a `just` recipe once the justfile exists) after the functional suite is green. A surviving mutant means the happy-path test didn't actually assert on that behavior — fix the assertion, don't just note the gap. Before accepting a mutant as unkillable, verify it's genuinely equivalent (no test could ever distinguish it from correct behavior — e.g. a case-only header change when the client library normalizes case) rather than just hard to test; check empirically, don't assume.

Any test that hits a real subprocess or network dependency it doesn't control (an `npx`-invoked CLI, a live service) gets `@pytest.mark.integration` and stays out of the mutation run — `just mutate` already excludes that marker via `pytest_add_cli_args`. Mutation testing invokes the suite far more times than `just test` does, and a real external dependency that's merely flaky under normal use becomes reliably flaky at that volume. `just test` still runs integration tests; only the mutation run skips them.

## CRAP score

Run `crap4py` against `src/` using the coverage file from the test run. The conventional risk threshold is **30** (`complexity² × (1−coverage)³ + complexity`). A function over 30 is high-risk by construction — it's both complex and undertested — and gets fixed before merging, not flagged for later: either reduce its complexity (usually by extracting the branching into smaller functions, which is what `domain/` logic should look like anyway) or bring its coverage up. A simple function can carry high complexity and still score low if it's well covered; the score is what tells you which lever to pull.
