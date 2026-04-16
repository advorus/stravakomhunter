from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional, Type

from strava_kom_checker.config import AppConfig
from strava_kom_checker.models import Location, to_json_dict
from strava_kom_checker.service import ForecastRequest, SegmentForecastService


def _number(payload: dict[str, Any], key: str, default: Optional[float] = None) -> float:
    value = payload.get(key, default)
    if value is None or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    return float(value)


def _int(payload: dict[str, Any], key: str, default: int) -> int:
    value = payload.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def parse_forecast_request(payload: dict[str, Any]) -> ForecastRequest:
    latitude = _number(payload, "latitude")
    longitude = _number(payload, "longitude")
    radius_meters = _number(payload, "radiusMeters", 10_000)
    limit = _int(payload, "limit", 10)

    if latitude < -90 or latitude > 90:
        raise ValueError("latitude must be between -90 and 90")
    if longitude < -180 or longitude > 180:
        raise ValueError("longitude must be between -180 and 180")
    if radius_meters <= 0 or radius_meters > 25_000:
        raise ValueError("radiusMeters must be between 1 and 25000")
    if limit <= 0 or limit > 25:
        raise ValueError("limit must be between 1 and 25")

    return ForecastRequest(
        location=Location(latitude, longitude),
        radius_meters=radius_meters,
        limit=limit,
    )


def build_forecast_response(
    config: AppConfig, forecast_service: SegmentForecastService, payload: dict[str, Any]
) -> dict[str, Any]:
    forecast_request = parse_forecast_request(payload)
    result = forecast_service.forecast_nearby_segments(forecast_request)

    return {
        "meta": {
            "units": {
                "speed": "m/s",
                "duration": "seconds",
                "power": "watts",
            },
            "assumptions": [
                "Uses Intervals.icu power curve as the sustainable power envelope.",
                "Approximates cornering from segment geometry because Strava explorer does not expose detailed turn-by-turn data.",
                "Uses current Open-Meteo conditions as the weather snapshot.",
            ],
            "port": config.port,
        },
        "data": to_json_dict(result),
    }


def build_handler(
    config: AppConfig, forecast_service: SegmentForecastService
) -> Type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            if self.path == "/health":
                self._json(HTTPStatus.OK, {"ok": True})
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

        def do_POST(self) -> None:
            if self.path != "/api/forecasts/nearby-segments":
                self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body or "{}")
                response = build_forecast_response(config, forecast_service, payload)
            except ValueError as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                return

            self._json(HTTPStatus.OK, response)

        def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def build_server(
    config: AppConfig, forecast_service: SegmentForecastService
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        ("0.0.0.0", config.port), build_handler(config, forecast_service)
    )
