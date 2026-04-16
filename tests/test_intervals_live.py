from __future__ import annotations

import os

import pytest

from strava_kom_checker.clients import IntervalsIcuClient


@pytest.mark.integration
def test_intervals_live_power_curve_request_succeeds():
    if os.getenv("RUN_LIVE_INTERVALS_TEST") != "1":
        pytest.skip("Set RUN_LIVE_INTERVALS_TEST=1 to run live Intervals.icu integration test")

    api_key = os.getenv("INTERVALS_ICU_API_KEY")
    athlete_id = os.getenv("INTERVALS_ICU_ATHLETE_ID")
    if not api_key or not athlete_id:
        pytest.skip("Missing INTERVALS_ICU_API_KEY or INTERVALS_ICU_ATHLETE_ID")

    client = IntervalsIcuClient(api_key=api_key)
    curve = client.get_power_curve(athlete_id=athlete_id)

    assert len(curve) > 0
    assert curve[0].duration_seconds > 0
    assert curve[0].power_watts > 0
