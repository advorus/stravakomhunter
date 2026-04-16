from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class FrontendError(RuntimeError):
    pass


def fetch_forecast(
    base_url: str,
    latitude: float,
    longitude: float,
    radius_meters: float,
    limit: int,
) -> dict[str, Any]:
    payload = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "radiusMeters": float(radius_meters),
        "limit": int(limit),
    }
    data = json.dumps(payload).encode("utf-8")
    url = f"{base_url.rstrip('/')}/api/forecasts/nearby-segments"
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8")
        detail = body
        if body:
            try:
                parsed = json.loads(body)
                detail = parsed.get("error", body)
            except json.JSONDecodeError:
                detail = body
        raise FrontendError(f"Backend returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise FrontendError(
            f"Could not reach backend at {base_url}. Is the API server running?"
        ) from error


def forecast_rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for forecast in response.get("data", {}).get("forecasts", []):
        rows.append(
            {
                "Segment": forecast.get("segmentName"),
                "Predicted Time (s)": round(float(forecast.get("predictedTimeSeconds", 0)), 1),
                "Avg Speed (m/s)": round(
                    float(forecast.get("estimatedAverageSpeedMps", 0)), 2
                ),
                "Sustainable Power (W)": round(
                    float(forecast.get("sustainablePowerWatts", 0)), 1
                ),
                "Weather Adjusted Power (W)": round(
                    float(forecast.get("weatherAdjustedPowerWatts", 0)), 1
                ),
                "Delta To KOM (s)": forecast.get("deltaToKomSeconds"),
            }
        )
    return rows
