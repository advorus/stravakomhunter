from __future__ import annotations

import math
from dataclasses import dataclass

from strava_kom_checker.clients import IntervalsIcuClient, StravaClient, WeatherClient
from strava_kom_checker.config import AppConfig
from strava_kom_checker.forecast import forecast_segment_time
from strava_kom_checker.models import (
    AthleteProfile,
    Location,
    SegmentContext,
    SegmentForecast,
    SegmentSummary,
    WeatherSnapshot,
)


@dataclass(frozen=True)
class ForecastRequest:
    location: Location
    radius_meters: float
    limit: int


@dataclass(frozen=True)
class ForecastResult:
    athlete: AthleteProfile
    weather: WeatherSnapshot
    forecasts: list[SegmentForecast]


def calculate_heading_degrees(segment: SegmentSummary) -> float:
    lat1 = math.radians(segment.start_lat_lng.latitude)
    lat2 = math.radians(segment.end_lat_lng.latitude)
    delta_lng = math.radians(
        segment.end_lat_lng.longitude - segment.start_lat_lng.longitude
    )
    y = math.sin(delta_lng) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        delta_lng
    )
    return math.degrees(math.atan2(y, x)) + 180


def estimate_corner_count(segment: SegmentSummary) -> int:
    turniness = max(abs(segment.average_grade_pct) / 4, 0.5)
    return round((segment.distance_meters / 400) * turniness)


def build_segment_context(segment: SegmentSummary) -> SegmentContext:
    return SegmentContext(
        segment=segment,
        heading_degrees=calculate_heading_degrees(segment),
        corner_count=estimate_corner_count(segment),
        corner_severity=min(abs(segment.average_grade_pct) / 12, 1),
        rolling_resistance_multiplier=1.1 if segment.average_grade_pct < -2 else 1,
    )


class SegmentForecastService:
    def __init__(
        self,
        config: AppConfig,
        intervals_client: IntervalsIcuClient,
        strava_client: StravaClient,
        weather_client: WeatherClient,
    ) -> None:
        self.config = config
        self.intervals_client = intervals_client
        self.strava_client = strava_client
        self.weather_client = weather_client

    def forecast_nearby_segments(self, request: ForecastRequest) -> ForecastResult:
        power_curve = self.intervals_client.get_power_curve(
            self.config.intervals_icu_athlete_id
        )
        weather = self.weather_client.get_current_weather(request.location)
        segments = self.strava_client.explore_segments_near(
            request.location, request.radius_meters
        )

        athlete = AthleteProfile(
            mass_kg=self.config.athlete_mass_kg,
            cda=self.config.athlete_cda,
            crr=self.config.athlete_crr,
            drivetrain_efficiency=self.config.athlete_drivetrain_efficiency,
            power_curve=power_curve,
        )

        selected_segments = sorted(
            segments, key=lambda segment: segment.elevation_gain_meters, reverse=True
        )[: request.limit]
        enriched_segments = [
            SegmentSummary(
                **{
                    **segment.__dict__,
                    "kom_time_seconds": self.strava_client.get_kom_time(segment.id),
                }
            )
            for segment in selected_segments
        ]
        forecasts = sorted(
            (
                forecast_segment_time(athlete, build_segment_context(segment), weather)
                for segment in enriched_segments
            ),
            key=lambda forecast: (
                forecast.delta_to_kom_seconds
                if forecast.delta_to_kom_seconds is not None
                else float("inf")
            ),
        )

        return ForecastResult(athlete=athlete, weather=weather, forecasts=forecasts)
