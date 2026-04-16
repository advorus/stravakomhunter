from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class PowerCurvePoint:
    duration_seconds: float
    power_watts: float


@dataclass(frozen=True)
class AthleteProfile:
    mass_kg: float
    cda: float
    crr: float
    drivetrain_efficiency: float
    power_curve: list[PowerCurvePoint]


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class SegmentSummary:
    id: int
    name: str
    distance_meters: float
    average_grade_pct: float
    elevation_gain_meters: float
    start_lat_lng: Location
    end_lat_lng: Location
    climb_category: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    start_elevation_meters: Optional[float] = None
    end_elevation_meters: Optional[float] = None
    kom_time_seconds: Optional[float] = None


@dataclass(frozen=True)
class SegmentContext:
    segment: SegmentSummary
    heading_degrees: float
    corner_count: int
    corner_severity: float
    rolling_resistance_multiplier: float


@dataclass(frozen=True)
class WeatherSnapshot:
    temperature_c: float
    wind_speed_mps: float
    wind_direction_degrees: float
    air_density_kg_per_m3: float
    precipitation_mm: float


@dataclass(frozen=True)
class SegmentForecast:
    segment_id: int
    segment_name: str
    predicted_time_seconds: float
    estimated_average_speed_mps: float
    sustainable_power_watts: float
    weather_adjusted_power_watts: float
    corner_penalty_seconds: float
    headwind_component_mps: float
    kom_time_seconds: Optional[float] = None
    delta_to_kom_seconds: Optional[float] = None


def to_camel_case(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


def to_json_dict(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            to_camel_case(field.name): to_json_dict(getattr(value, field.name))
            for field in fields(value)
            for item in [getattr(value, field.name)]
            if item is not None
        }

    if isinstance(value, list):
        return [to_json_dict(item) for item in value]

    if isinstance(value, dict):
        return {key: to_json_dict(item) for key, item in value.items()}

    return value
