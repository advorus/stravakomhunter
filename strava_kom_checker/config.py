from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional


@dataclass(frozen=True)
class AppConfig:
    port: int
    intervals_icu_api_key: str
    intervals_icu_athlete_id: str
    strava_access_token: str
    strava_client_id: Optional[str]
    strava_client_secret: Optional[str]
    strava_refresh_token: Optional[str]
    athlete_mass_kg: float
    athlete_cda: float
    athlete_crr: float
    athlete_drivetrain_efficiency: float


def _unquote(value: str) -> str:
    trimmed = value.strip()
    if len(trimmed) >= 2 and trimmed[0] == trimmed[-1] and trimmed[0] in ("'", '"'):
        return trimmed[1:-1]
    return trimmed


def load_local_env(path: str = ".env") -> None:
    env_path = Path.cwd() / path
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
            continue

        key, value = trimmed.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = _unquote(value)


def _required(env: Mapping[str, str], key: str) -> str:
    value = env.get(key)
    if value:
        return value
    raise KeyError(key)


def _optional(env: Mapping[str, str], key: str) -> Optional[str]:
    return env.get(key) or None


def _number(env: Mapping[str, str], key: str, default: float) -> float:
    value = env.get(key)
    return default if value in (None, "") else float(value)


def _positive_number(env: Mapping[str, str], key: str, default: float) -> float:
    value = _number(env, key, default)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def load_config(env: Optional[Mapping[str, str]] = None) -> AppConfig:
    source = os.environ if env is None else env
    missing: list[str] = []

    try:
        intervals_key = _required(source, "INTERVALS_ICU_API_KEY")
    except KeyError:
        missing.append("INTERVALS_ICU_API_KEY")
        intervals_key = ""

    try:
        athlete_id = _required(source, "INTERVALS_ICU_ATHLETE_ID")
    except KeyError:
        missing.append("INTERVALS_ICU_ATHLETE_ID")
        athlete_id = ""

    try:
        strava_token = _required(source, "STRAVA_ACCESS_TOKEN")
    except KeyError:
        missing.append("STRAVA_ACCESS_TOKEN")
        strava_token = ""

    if missing:
        joined = ", ".join(missing)
        raise ValueError(
            f"Missing required environment variables: {joined}. "
            "Check that .env exists and contains the values listed in .env.example."
        )

    port = int(_number(source, "PORT", 3000))
    if port <= 0:
        raise ValueError("PORT must be positive")

    drivetrain_efficiency = _positive_number(
        source, "ATHLETE_DRIVETRAIN_EFFICIENCY", 0.975
    )
    if drivetrain_efficiency > 1:
        raise ValueError("ATHLETE_DRIVETRAIN_EFFICIENCY must be 1 or lower")

    return AppConfig(
        port=port,
        intervals_icu_api_key=intervals_key,
        intervals_icu_athlete_id=athlete_id,
        strava_access_token=strava_token,
        strava_client_id=_optional(source, "STRAVA_CLIENT_ID"),
        strava_client_secret=_optional(source, "STRAVA_CLIENT_SECRET"),
        strava_refresh_token=_optional(source, "STRAVA_REFRESH_TOKEN"),
        athlete_mass_kg=_positive_number(source, "ATHLETE_MASS_KG", 75),
        athlete_cda=_positive_number(source, "ATHLETE_CDA", 0.32),
        athlete_crr=_positive_number(source, "ATHLETE_CRR", 0.005),
        athlete_drivetrain_efficiency=drivetrain_efficiency,
    )
