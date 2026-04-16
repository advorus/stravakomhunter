from strava_kom_checker.forecast import forecast_segment_time
from strava_kom_checker.models import (
    AthleteProfile,
    Location,
    PowerCurvePoint,
    SegmentContext,
    SegmentSummary,
    WeatherSnapshot,
)


athlete = AthleteProfile(
    mass_kg=75,
    cda=0.32,
    crr=0.005,
    drivetrain_efficiency=0.975,
    power_curve=[
        PowerCurvePoint(duration_seconds=30, power_watts=520),
        PowerCurvePoint(duration_seconds=60, power_watts=470),
        PowerCurvePoint(duration_seconds=300, power_watts=360),
        PowerCurvePoint(duration_seconds=1200, power_watts=290),
    ],
)

base_segment = SegmentContext(
    segment=SegmentSummary(
        id=1,
        name="Test Climb",
        distance_meters=2500,
        average_grade_pct=5,
        elevation_gain_meters=125,
        kom_time_seconds=360,
        start_lat_lng=Location(latitude=51.5, longitude=-0.1),
        end_lat_lng=Location(latitude=51.51, longitude=-0.11),
    ),
    heading_degrees=180,
    corner_count=2,
    corner_severity=0.3,
    rolling_resistance_multiplier=1,
)

calm_weather = WeatherSnapshot(
    temperature_c=15,
    wind_speed_mps=0,
    wind_direction_degrees=0,
    air_density_kg_per_m3=1.225,
    precipitation_mm=0,
)


def test_forecast_segment_time_produces_forecast_and_delta_to_kom():
    forecast = forecast_segment_time(athlete, base_segment, calm_weather)

    assert forecast.predicted_time_seconds > 200
    assert forecast.predicted_time_seconds < 900
    assert forecast.delta_to_kom_seconds is not None
    assert forecast.corner_penalty_seconds > 0


def test_forecast_segment_time_slows_the_rider_down_in_a_headwind():
    headwind = forecast_segment_time(
        athlete,
        base_segment,
        WeatherSnapshot(
            **{**calm_weather.__dict__, "wind_speed_mps": 4, "wind_direction_degrees": 180}
        ),
    )
    tailwind = forecast_segment_time(
        athlete,
        base_segment,
        WeatherSnapshot(
            **{**calm_weather.__dict__, "wind_speed_mps": 4, "wind_direction_degrees": 0}
        ),
    )

    assert headwind.predicted_time_seconds > tailwind.predicted_time_seconds
