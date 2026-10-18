"""The gate is shared by independent engines, not just Python threads/globals."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import create_engine, text

from admission import Busy, itunes_slot


def test_only_one_itunes_search_across_instances(tmp_path):
    url = f"sqlite:///{tmp_path / 'gate.db'}"
    entered, release = Event(), Event()

    def active():
        with itunes_slot(create_engine(url)):
            entered.set()
            assert release.wait(10)

    def competing(_):
        with pytest.raises(Busy) as busy:
            with itunes_slot(create_engine(url)):
                pytest.fail("A second instance must not start store work")
        assert 1 <= busy.value.retry_after <= 60

    with ThreadPoolExecutor(max_workers=12) as pool:
        first = pool.submit(active)
        assert entered.wait(5)
        try:
            list(pool.map(competing, range(10)))
        finally:
            release.set()
        first.result()


def test_completion_retains_six_second_cooldown(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'gate.db'}")
    with itunes_slot(engine):
        pass
    with pytest.raises(Busy) as busy:
        with itunes_slot(engine):
            pytest.fail("Fast searches must not exceed the rate budget")
    assert 5 <= busy.value.retry_after <= 6


def test_failed_search_releases_slot_but_keeps_budget(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'gate.db'}")
    with pytest.raises(RuntimeError):
        with itunes_slot(engine):
            raise RuntimeError("Provider failed")
    with engine.connect() as connection:
        owner, lease, next_allowed = connection.execute(
            text("SELECT owner, lease_until, next_allowed FROM itunes_search_admission")).one()
    assert owner is None and lease == 0 and next_allowed > 0


def test_expired_lease_recovers_and_old_owner_cannot_release_new_owner(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'gate.db'}")
    old = itunes_slot(engine)
    old.__enter__()
    with engine.begin() as connection:
        # Simulate a Lambda killed after admission, without waiting 60 seconds.
        connection.execute(text("UPDATE itunes_search_admission SET lease_until = 0, next_allowed = 0"))
    with itunes_slot(create_engine(str(engine.url))):
        old.__exit__(None, None, None)
        with engine.connect() as connection:
            assert connection.execute(text("SELECT owner FROM itunes_search_admission")).scalar_one()
