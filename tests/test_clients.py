from strava_kom_checker.clients import (
    IntervalsIcuClient,
    StravaClient,
    parse_strava_duration_to_seconds,
)


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
