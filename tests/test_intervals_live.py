from __future__ import annotations

import os
import urllib.parse
import urllib.request
import json

import pytest

from strava_kom_checker.clients import IntervalsIcuClient, StravaClient, WeatherClient
from strava_kom_checker.models import Location


def _live_enabled() -> bool:
    return os.getenv("RUN_LIVE_API_TESTS") == "1"


def _require_live_mode() -> None:
    if not _live_enabled():
        pytest.skip("Set RUN_LIVE_API_TESTS=1 to run live external API integration tests")


def _refresh_strava_access_token_if_possible() -> str | None:
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
    if not (client_id and client_secret and refresh_token):
        return None

    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://www.strava.com/oauth/token",
        data=body,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("access_token")


@pytest.mark.integration
def test_intervals_live_power_curve_request_succeeds():
    _require_live_mode()

    api_key = os.getenv("INTERVALS_ICU_API_KEY")
    athlete_id = os.getenv("INTERVALS_ICU_ATHLETE_ID")
    if not api_key or not athlete_id:
        pytest.skip("Missing INTERVALS_ICU_API_KEY or INTERVALS_ICU_ATHLETE_ID")

    client = IntervalsIcuClient(api_key=api_key)
    curve = client.get_power_curve(athlete_id=athlete_id)

    assert len(curve) > 0
    assert curve[0].duration_seconds > 0
    assert curve[0].power_watts > 0


@pytest.mark.integration
def test_strava_live_segment_explore_and_kom_lookup_succeeds():
    _require_live_mode()

    access_token = (
        _refresh_strava_access_token_if_possible() or os.getenv("STRAVA_ACCESS_TOKEN")
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


@pytest.mark.integration
def test_open_meteo_live_weather_request_succeeds():
    _require_live_mode()

    client = WeatherClient()
    weather = client.get_current_weather(Location(latitude=51.5074, longitude=-0.1278))

    assert isinstance(weather.temperature_c, (int, float))
    assert isinstance(weather.wind_speed_mps, (int, float))
