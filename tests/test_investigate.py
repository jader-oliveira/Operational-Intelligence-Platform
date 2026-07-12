from datetime import datetime, timedelta, timezone

from boip.core.investigate import RECENCY_HALF_LIFE_HOURS, _recency_weight


def test_recency_weight_is_one_at_reference_time():
    now = datetime.now(timezone.utc)
    assert _recency_weight(now, now) == 1.0


def test_recency_weight_halves_at_half_life():
    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=RECENCY_HALF_LIFE_HOURS)
    assert abs(_recency_weight(past, now) - 0.5) < 1e-9


def test_recency_weight_symmetric_around_reference():
    now = datetime.now(timezone.utc)
    before = now - timedelta(hours=3)
    after = now + timedelta(hours=3)
    assert abs(_recency_weight(before, now) - _recency_weight(after, now)) < 1e-9


def test_recency_weight_decays_monotonically():
    now = datetime.now(timezone.utc)
    w1 = _recency_weight(now - timedelta(hours=1), now)
    w2 = _recency_weight(now - timedelta(hours=10), now)
    assert w1 > w2
