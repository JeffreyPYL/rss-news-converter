from __future__ import annotations

from datetime import UTC, datetime

from news_digest.infrastructure.state.run_state import DEFAULT_LOOKBACK, RunState


def test_normal_run_covers_since_last_success(tmp_path):
    state = RunState(tmp_path / "state.json")
    last_success = datetime(2026, 8, 27, 7, 0, 0, tzinfo=UTC)
    state.record_success(at=last_success)

    since = state.lookback_since(now=datetime(2026, 8, 28, 7, 0, 0, tzinfo=UTC))

    assert since == last_success


def test_first_ever_run_defaults_to_48_hours(tmp_path):
    state = RunState(tmp_path / "state.json")
    now = datetime(2026, 8, 28, 7, 0, 0, tzinfo=UTC)

    since = state.lookback_since(now=now)

    assert since == now - DEFAULT_LOOKBACK


def test_missed_scheduled_run_self_heals(tmp_path):
    state = RunState(tmp_path / "state.json")
    last_success = datetime(2026, 8, 26, 7, 0, 0, tzinfo=UTC)
    state.record_success(at=last_success)

    since = state.lookback_since(now=datetime(2026, 8, 28, 7, 0, 0, tzinfo=UTC))

    assert since == last_success


def test_record_success_with_no_argument_uses_utc_not_naive_local_time(tmp_path):
    state = RunState(tmp_path / "state.json")

    state.record_success()

    recorded = state.last_success()
    assert recorded.tzinfo is not None
    assert recorded.utcoffset().total_seconds() == 0


def test_record_success_creates_nested_directories_that_dont_exist_yet(tmp_path):
    state = RunState(tmp_path / "a" / "b" / "state.json")

    state.record_success(at=datetime(2026, 8, 28, 7, 0, 0, tzinfo=UTC))

    assert (tmp_path / "a" / "b" / "state.json").exists()


def test_record_success_twice_does_not_raise(tmp_path):
    state = RunState(tmp_path / "state.json")

    state.record_success(at=datetime(2026, 8, 27, 7, 0, 0, tzinfo=UTC))
    state.record_success(at=datetime(2026, 8, 28, 7, 0, 0, tzinfo=UTC))

    assert state.last_success() == datetime(2026, 8, 28, 7, 0, 0, tzinfo=UTC)


def test_empty_state_file_self_heals_instead_of_crashing(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("")
    state = RunState(path)

    assert state.last_success() is None


def test_corrupt_state_file_self_heals_instead_of_crashing(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{not valid json")
    state = RunState(path)

    now = datetime(2026, 8, 28, 7, 0, 0, tzinfo=UTC)
    assert state.lookback_since(now=now) == now - DEFAULT_LOOKBACK
