from strava_kom_checker.config import AppConfig
from strava_kom_checker.models import Location, PowerCurvePoint, SegmentSummary, WeatherSnapshot
from strava_kom_checker.service import ForecastRequest, SegmentForecastService


config = AppConfig(
    port=3000,
    intervals_icu_api_key="intervals-key",
    intervals_icu_athlete_id="athlete-1",
    strava_access_token="strava-token",
    strava_client_id="client-id",
    strava_client_secret="client-secret",
    strava_refresh_token="refresh-token",
    athlete_mass_kg=75,
    athlete_cda=0.32,
    athlete_crr=0.005,
    athlete_drivetrain_efficiency=0.975,
)


class FakeIntervalsClient:
    def get_power_curve(self, athlete_id):
        assert athlete_id == "athlete-1"
        return [
            PowerCurvePoint(duration_seconds=60, power_watts=420),
            PowerCurvePoint(duration_seconds=300, power_watts=330),
        ]


class FakeStravaClient:
    def __init__(self):
        self.kom_times = iter([180, 220])

    def explore_segments_near(self, location, radius_meters):
        return [
            SegmentSummary(
                id=100,
                name="Segment A",
                distance_meters=1600,
                average_grade_pct=3,
                elevation_gain_meters=48,
                start_lat_lng=Location(latitude=51.5, longitude=-0.1),
                end_lat_lng=Location(latitude=51.51, longitude=-0.11),
            ),
            SegmentSummary(
                id=200,
                name="Segment B",
                distance_meters=900,
                average_grade_pct=8,
                elevation_gain_meters=72,
                start_lat_lng=Location(latitude=51.52, longitude=-0.1),
                end_lat_lng=Location(latitude=51.53, longitude=-0.11),
            ),
        ]

    def get_kom_time(self, segment_id):
        return next(self.kom_times)


class FakeWeatherClient:
    def get_current_weather(self, location):
        return WeatherSnapshot(
            temperature_c=12,
            wind_speed_mps=2,
            wind_direction_degrees=90,
            air_density_kg_per_m3=1.23,
            precipitation_mm=0,
        )


def test_segment_forecast_service_combines_data_into_sorted_forecasts():
    service = SegmentForecastService(
        config, FakeIntervalsClient(), FakeStravaClient(), FakeWeatherClient()
    )
    result = service.forecast_nearby_segments(
        ForecastRequest(
            location=Location(latitude=51.5, longitude=-0.1),
            radius_meters=10_000,
            limit=2,
        )
    )

    assert len(result.athlete.power_curve) == 2
    assert len(result.forecasts) == 2
    assert result.forecasts[0].delta_to_kom_seconds <= result.forecasts[1].delta_to_kom_seconds
