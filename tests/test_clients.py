from strava_kom_checker.clients import IntervalsIcuClient, StravaClient


def test_strava_client_returns_none_when_leaderboard_is_forbidden():
    def fetcher(url, headers):
        return 403, {}

    client = StravaClient("strava-token", fetcher=fetcher)

    assert client.get_kom_time(123) is None


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
