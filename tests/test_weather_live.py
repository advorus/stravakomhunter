from __future__ import annotations

import pytest

from strava_kom_checker.clients import WeatherClient
from strava_kom_checker.models import Location
from tests.live_test_utils import require_live_mode


@pytest.mark.integration
def test_open_meteo_live_weather_request_succeeds():
    require_live_mode()

    client = WeatherClient()
    weather = client.get_current_weather(Location(latitude=51.5074, longitude=-0.1278))

    assert isinstance(weather.temperature_c, (int, float))
    assert isinstance(weather.wind_speed_mps, (int, float))
