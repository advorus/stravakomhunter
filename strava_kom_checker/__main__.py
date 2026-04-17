from __future__ import annotations

from strava_kom_checker.clients import IntervalsIcuClient, StravaClient, WeatherClient
from strava_kom_checker.config import load_config, load_local_env
from strava_kom_checker.server import build_server
from strava_kom_checker.service import SegmentForecastService


def main() -> None:
    load_local_env()
    config = load_config()
    service = SegmentForecastService(
        config=config,
        intervals_client=IntervalsIcuClient(config.intervals_icu_api_key),
        strava_client=StravaClient(
            access_token=config.strava_access_token,
            client_id=config.strava_client_id,
            client_secret=config.strava_client_secret,
            refresh_token=config.strava_refresh_token,
        ),
        weather_client=WeatherClient(),
    )
    server = build_server(config, service)
    print(f"Strava KOM Checker listening on {config.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
