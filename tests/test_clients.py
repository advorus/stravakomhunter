from strava_kom_checker.clients import StravaClient


def test_strava_client_returns_none_when_leaderboard_is_forbidden():
    def fetcher(url, headers):
        return 403, {}

    client = StravaClient("strava-token", fetcher=fetcher)

    assert client.get_kom_time(123) is None
