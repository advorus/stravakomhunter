from __future__ import annotations

import math
from typing import Optional

from strava_kom_checker.models import (
    AthleteProfile,
    PowerCurvePoint,
    SegmentContext,
    SegmentForecast,
    WeatherSnapshot,
)

GRAVITY = 9.80665


def interpolate_power(curve: list[PowerCurvePoint], duration_seconds: float) -> float:
    sorted_curve = sorted(curve, key=lambda point: point.duration_seconds)
    if not sorted_curve:
        raise ValueError("Athlete power curve cannot be empty")

    first = sorted_curve[0]
    if duration_seconds <= first.duration_seconds:
        return first.power_watts

    last = sorted_curve[-1]
    if duration_seconds >= last.duration_seconds:
        return last.power_watts

    for previous, next_point in zip(sorted_curve, sorted_curve[1:]):
        if duration_seconds <= next_point.duration_seconds:
            ratio = (duration_seconds - previous.duration_seconds) / (
                next_point.duration_seconds - previous.duration_seconds
            )
            return previous.power_watts + ratio * (
                next_point.power_watts - previous.power_watts
            )

    return last.power_watts


def solve_velocity(
    power_watts: float,
    athlete: AthleteProfile,
    segment: SegmentContext,
    weather: WeatherSnapshot,
) -> float:
    grade = segment.segment.average_grade_pct / 100
    crr = athlete.crr * segment.rolling_resistance_multiplier
    heading_radians = math.radians(segment.heading_degrees)
    wind_radians = math.radians(weather.wind_direction_degrees)
    headwind_component = weather.wind_speed_mps * math.cos(
        wind_radians - heading_radians
    )
    effective_power = power_watts * athlete.drivetrain_efficiency

    speed = 6.0
    for _ in range(30):
        relative_air_speed = max(speed + headwind_component, 0.1)
        rolling_force = athlete.mass_kg * GRAVITY * crr
        gravity_force = athlete.mass_kg * GRAVITY * grade
        aerodynamic_force = (
            0.5
            * weather.air_density_kg_per_m3
            * athlete.cda
            * relative_air_speed
            * relative_air_speed
        )
        total_force = max(rolling_force + gravity_force + aerodynamic_force, 1)
        speed = max(effective_power / total_force, 0.5)

    return speed


def forecast_segment_time(
    athlete: AthleteProfile,
    segment: SegmentContext,
    weather: WeatherSnapshot,
    min_duration_seconds: float = 30,
    max_iterations: int = 7,
) -> SegmentForecast:
    heading_radians = math.radians(segment.heading_degrees)
    wind_radians = math.radians(weather.wind_direction_degrees)
    headwind_component_mps = weather.wind_speed_mps * math.cos(
        wind_radians - heading_radians
    )

    estimated_duration_seconds = max(
        segment.segment.distance_meters / 7, min_duration_seconds
    )
    sustainable_power_watts = interpolate_power(
        athlete.power_curve, estimated_duration_seconds
    )

    for _ in range(max_iterations):
        sustainable_power_watts = interpolate_power(
            athlete.power_curve, estimated_duration_seconds
        )
        weather_adjusted_power_watts = max(
            sustainable_power_watts - weather.precipitation_mm * 1.5, 50
        )
        speed = solve_velocity(weather_adjusted_power_watts, athlete, segment, weather)
        estimated_duration_seconds = max(
            segment.segment.distance_meters / speed, min_duration_seconds
        )

    corner_penalty_seconds = segment.corner_count * (
        1.5 + 2 * segment.corner_severity
    )
    predicted_time_seconds = estimated_duration_seconds + corner_penalty_seconds
    weather_adjusted_power_watts = max(
        sustainable_power_watts - weather.precipitation_mm * 1.5, 50
    )

    delta_to_kom_seconds: Optional[float] = None
    if segment.segment.kom_time_seconds is not None:
        delta_to_kom_seconds = predicted_time_seconds - segment.segment.kom_time_seconds

    return SegmentForecast(
        segment_id=segment.segment.id,
        segment_name=segment.segment.name,
        predicted_time_seconds=predicted_time_seconds,
        estimated_average_speed_mps=segment.segment.distance_meters
        / predicted_time_seconds,
        sustainable_power_watts=sustainable_power_watts,
        weather_adjusted_power_watts=weather_adjusted_power_watts,
        corner_penalty_seconds=corner_penalty_seconds,
        headwind_component_mps=headwind_component_mps,
        kom_time_seconds=segment.segment.kom_time_seconds,
        delta_to_kom_seconds=delta_to_kom_seconds,
    )
