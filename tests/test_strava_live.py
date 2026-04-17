from __future__ import annotations

import os

import pytest

from strava_kom_checker.clients import StravaClient
from strava_kom_checker.models import Location
from tests.live_test_utils import require_live_mode, refresh_strava_access_token_if_possible


@pytest.mark.integration
def test_strava_live_segment_explore_and_kom_lookup_succeeds():
    require_live_mode()

    access_token = (
        refresh_strava_access_token_if_possible() or os.getenv("STRAVA_ACCESS_TOKEN")
    )
    if not access_token:
        pytest.skip(
            "Missing Strava credentials: provide STRAVA_ACCESS_TOKEN or refresh-token credentials"
        )

    client = StravaClient(access_token=access_token)
    location = Location(latitude=51.5074, longitude=-0.1278)
    segments = client.explore_segments_near(location=location, radius_meters=10_000)

    assert len(segments) > 0

    kom_values = [client.get_kom_time(segment.id) for segment in segments[:10]]
    assert any(value is not None for value in kom_values)
