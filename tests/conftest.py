from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _isolate_from_real_dotenv(monkeypatch, tmp_path):
    """`Settings` reads `.env` from the current working directory, and real
    `NEWS_DIGEST_*` env vars always win over `.env` values. Without this, a
    real `.env` a developer created for local use (per the README) — or,
    since `just` loads `.env` into the real environment (`set dotenv-load`),
    the real env vars it exports — would leak into every test that doesn't
    explicitly set every field, silently changing "unconfigured" tests into
    "configured" ones."""
    monkeypatch.chdir(tmp_path)
    for key in list(os.environ):
        if key.startswith("NEWS_DIGEST_"):
            monkeypatch.delenv(key, raising=False)
