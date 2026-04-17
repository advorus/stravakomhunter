from __future__ import annotations

import base64
import json
from typing import Any, Callable, Optional
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from strava_kom_checker.models import Location, PowerCurvePoint, SegmentSummary, WeatherSnapshot

JsonFetcher = Callable[[str, Optional[dict[str, str]]], tuple[int, dict[str, Any]]]


def fetch_json(url: str, headers: Optional[dict[str, str]] = None) -> tuple[int, dict[str, Any]]:
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8")
        return error.code, json.loads(body) if body else {}


def parse_strava_duration_to_seconds(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    text = value.strip().lower()
    if not text:
        return None

    if text.endswith("s"):
        try:
            return float(text[:-1])
        except ValueError:
            return None

    parts = text.split(":")
    try:
        values = [float(part) for part in parts]
    except ValueError:
        return None

    if len(values) == 2:
        minutes, seconds = values
        return minutes * 60 + seconds
    if len(values) == 3:
        hours, minutes, seconds = values
        return hours * 3600 + minutes * 60 + seconds
    return None


class IntervalsIcuClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://intervals.icu/api/v1",
        fetcher: JsonFetcher = fetch_json,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.fetcher = fetcher

    def get_power_curve(self, athlete_id: str) -> list[PowerCurvePoint]:
        credentials = base64.b64encode(f"API_KEY:{self.api_key}".encode()).decode()
        status, payload = self.fetcher(
            f"{self.base_url}/athlete/{athlete_id}/power-curves?{urlencode({'curves': '1y', 'type': 'Ride'})}",
            {"Authorization": f"Basic {credentials}", "Accept": "application/json"},
        )
        if status < 200 or status >= 300:
            raise RuntimeError(f"Intervals.icu request failed with {status}")

        bests = []
        list_payload = payload.get("list")
        if isinstance(list_payload, list) and list_payload:
            first_curve = list_payload[0]
            secs = first_curve.get("secs") if isinstance(first_curve, dict) else None
            values = first_curve.get("values") if isinstance(first_curve, dict) else None
            if isinstance(secs, list) and isinstance(values, list):
                bests = [
                    PowerCurvePoint(duration_seconds=int(duration), power_watts=float(watts))
                    for duration, watts in zip(secs, values)
                    if isinstance(duration, (int, float))
                    and isinstance(watts, (int, float))
                    and duration > 0
                    and watts > 0
                ]

        if not bests:
            bests = [
                PowerCurvePoint(entry["secs"], entry["watts"])
                for entry in payload.get("bests", [])
                if entry.get("secs") and entry.get("watts")
            ]
        if bests:
            return sorted(bests, key=lambda point: point.duration_seconds)

        season_metrics = [
            PowerCurvePoint(entry["duration"], entry["value"])
            for entry in payload.get("seasonMetrics", [])
            if entry.get("type") == "power_curve"
            and isinstance(entry.get("value"), (int, float))
            and isinstance(entry.get("duration"), (int, float))
        ]
        if not season_metrics:
            raise RuntimeError("Intervals.icu response did not include a power curve payload")

        return sorted(season_metrics, key=lambda point: point.duration_seconds)


class StravaClient:
    def __init__(
        self,
        access_token: str,
        base_url: str = "https://www.strava.com/api/v3",
        fetcher: JsonFetcher = fetch_json,
    ) -> None:
        self.access_token = access_token
        self.base_url = base_url
        self.fetcher = fetcher

    def explore_segments_near(
        self, location: Location, radius_meters: float
    ) -> list[SegmentSummary]:
        delta = radius_meters / 111_320
        bounds = ",".join(
            str(value)
            for value in (
                location.latitude - delta,
                location.longitude - delta,
                location.latitude + delta,
                location.longitude + delta,
            )
        )
        status, payload = self.fetcher(
            f"{self.base_url}/segments/explore?{urlencode({'bounds': bounds})}",
            {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            },
        )
        if status < 200 or status >= 300:
            raise RuntimeError(f"Strava segment explore failed with {status}")

        return [
            SegmentSummary(
                id=segment["id"],
                name=segment["name"],
                distance_meters=segment["distance"],
                average_grade_pct=segment["avg_grade"],
                elevation_gain_meters=segment["elev_difference"],
                climb_category=segment.get("climb_category"),
                city=segment.get("city"),
                state=segment.get("state"),
                country=segment.get("country"),
                start_lat_lng=Location(segment["start_latlng"][0], segment["start_latlng"][1]),
                end_lat_lng=Location(segment["end_latlng"][0], segment["end_latlng"][1]),
            )
            for segment in payload.get("segments", [])
        ]

    def get_kom_time(self, segment_id: int) -> Optional[float]:
        segment_status, segment_payload = self.fetcher(
            f"{self.base_url}/segments/{segment_id}",
            {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            },
        )
        if 200 <= segment_status < 300:
            xoms = segment_payload.get("xoms") or {}
            kom_seconds = parse_strava_duration_to_seconds(xoms.get("kom"))
            if kom_seconds is not None:
                return kom_seconds
        elif segment_status not in (403, 404):
            raise RuntimeError(f"Strava segment detail lookup failed with {segment_status}")

        status, payload = self.fetcher(
            f"{self.base_url}/segments/{segment_id}/leaderboard?top_results_limit=1",
            {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            },
        )
        if status in (403, 404):
            return None
        if status < 200 or status >= 300:
            raise RuntimeError(f"Strava leaderboard lookup failed with {status}")

        entries = payload.get("entries") or []
        return entries[0].get("elapsed_time") if entries else None


class WeatherClient:
    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com/v1/forecast",
        fetcher: JsonFetcher = fetch_json,
    ) -> None:
        self.base_url = base_url
        self.fetcher = fetcher

    def get_current_weather(self, location: Location) -> WeatherSnapshot:
        query = urlencode(
            {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "current": "temperature_2m,wind_speed_10m,wind_direction_10m,precipitation",
                "wind_speed_unit": "ms",
            }
        )
        status, payload = self.fetcher(f"{self.base_url}?{query}", None)
        if status < 200 or status >= 300:
            raise RuntimeError(f"Open-Meteo request failed with {status}")

        current = payload.get("current") or {}
        temperature_c = current.get("temperature_2m", 15)
        pressure_pa = 101_325
        air_density_kg_per_m3 = pressure_pa / (287.05 * (temperature_c + 273.15))

        return WeatherSnapshot(
            temperature_c=temperature_c,
            wind_speed_mps=current.get("wind_speed_10m", 0),
            wind_direction_degrees=current.get("wind_direction_10m", 0),
            air_density_kg_per_m3=air_density_kg_per_m3,
            precipitation_mm=current.get("precipitation", 0),
        )
