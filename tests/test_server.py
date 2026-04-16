from strava_kom_checker.config import AppConfig
from strava_kom_checker.models import (
    AthleteProfile,
    PowerCurvePoint,
    SegmentForecast,
    WeatherSnapshot,
)
from strava_kom_checker.server import build_forecast_response
from strava_kom_checker.service import ForecastResult


config = AppConfig(
    port=0,
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


class FakeForecastService:
    def forecast_nearby_segments(self, request):
        return ForecastResult(
            athlete=AthleteProfile(
                mass_kg=75,
                cda=0.32,
                crr=0.005,
                drivetrain_efficiency=0.975,
                power_curve=[PowerCurvePoint(duration_seconds=300, power_watts=330)],
            ),
            weather=WeatherSnapshot(
                temperature_c=12,
                wind_speed_mps=2,
                wind_direction_degrees=90,
                air_density_kg_per_m3=1.23,
                precipitation_mm=0,
            ),
            forecasts=[
                SegmentForecast(
                    segment_id=1,
                    segment_name="Example Segment",
                    predicted_time_seconds=210,
                    estimated_average_speed_mps=7.1,
                    sustainable_power_watts=330,
                    weather_adjusted_power_watts=330,
                    corner_penalty_seconds=5,
                    headwind_component_mps=1,
                    kom_time_seconds=190,
                    delta_to_kom_seconds=20,
                )
            ],
        )


def test_forecast_response_returns_forecast_results():
    body = build_forecast_response(
        config,
        FakeForecastService(),
        {
            "latitude": 51.5,
            "longitude": -0.1,
            "radiusMeters": 5000,
            "limit": 5,
        },
    )

    assert body["meta"]["port"] == 0
    assert body["data"]["forecasts"][0]["segmentName"] == "Example Segment"
