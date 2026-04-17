from strava_kom_checker.clients import (
    IntervalsIcuClient,
    StravaClient,
    parse_strava_duration_to_seconds,
)
from strava_kom_checker.models import Location


def test_strava_client_returns_none_when_leaderboard_is_forbidden():
    def fetcher(url, headers):
        return 403, {}

    client = StravaClient("strava-token", fetcher=fetcher)

    assert client.get_kom_time(123) is None


def test_strava_client_uses_segment_detail_xoms_for_kom_time():
    def fetcher(url, headers):
        if "/segments/123/leaderboard" in url:
            raise AssertionError("leaderboard endpoint should not be called when xoms.kom is available")
        return 200, {"xoms": {"kom": "1:48"}}

    client = StravaClient("strava-token", fetcher=fetcher)
    assert client.get_kom_time(123) == 108.0


def test_parse_strava_duration_to_seconds_handles_supported_formats():
    assert parse_strava_duration_to_seconds("2s") == 2.0
    assert parse_strava_duration_to_seconds("1:48") == 108.0
    assert parse_strava_duration_to_seconds("1:02:03") == 3723.0


def test_strava_client_refreshes_on_401_and_retries():
    seen_auth_headers = []

    def fetcher(url, headers):
        seen_auth_headers.append(headers["Authorization"])
        if headers["Authorization"] == "Bearer stale-token":
            return 401, {}
        return 200, {"segments": []}

    def token_refresher(client_id, client_secret, refresh_token):
        assert client_id == "client-id"
        assert client_secret == "client-secret"
        assert refresh_token == "refresh-token"
        return {"access_token": "fresh-token", "refresh_token": "new-refresh-token"}

    client = StravaClient(
        access_token="stale-token",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        fetcher=fetcher,
        token_refresher=token_refresher,
    )
    segments = client.explore_segments_near(Location(51.5, -0.1), radius_meters=5000)

    assert segments == []
    assert seen_auth_headers == ["Bearer stale-token", "Bearer fresh-token"]
    assert client.access_token == "fresh-token"
    assert client.refresh_token == "new-refresh-token"


def test_strava_client_without_refresh_credentials_still_fails_on_401():
    def fetcher(url, headers):
        return 401, {}

    client = StravaClient(access_token="stale-token", fetcher=fetcher)

    try:
        client.explore_segments_near(Location(51.5, -0.1), radius_meters=5000)
        raise AssertionError("Expected RuntimeError for 401 without refresh credentials")
    except RuntimeError as error:
        assert "401" in str(error)


def test_intervals_client_uses_power_curves_endpoint_and_parses_curve_list():
    captured = {}

    def fetcher(url, headers):
        captured["url"] = url
        captured["headers"] = headers
        return 200, {"list": [{"secs": [1, 5, 10], "values": [900, 600, 500]}]}

    client = IntervalsIcuClient("intervals-key", fetcher=fetcher)
    curve = client.get_power_curve("i123")

    assert "/athlete/i123/power-curves" in captured["url"]
    assert "curves=1y" in captured["url"]
    assert "type=Ride" in captured["url"]
    assert captured["headers"]["Authorization"].startswith("Basic ")
    assert [point.duration_seconds for point in curve] == [1, 5, 10]
    assert [point.power_watts for point in curve] == [900.0, 600.0, 500.0]
