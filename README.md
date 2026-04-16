# Strava KOM Checker

A Python service that pulls an athlete power curve from Intervals.icu, discovers nearby Strava segments, applies a physics-based forecast, and compares the predicted segment time with the current KOM.

## What this first version does

- pulls your power curve from Intervals.icu
- discovers nearby Strava segments with Strava's segment explorer
- retrieves leaderboard pace where available
- models segment time from rider mass, CdA, rolling resistance, grade, wind, and rain
- adds a cornering penalty heuristic so we can evolve toward better geometry-aware models later
- exposes the result through a simple HTTP API

## API design

`POST /api/forecasts/nearby-segments`

Example payload:

```json
{
  "latitude": 51.5074,
  "longitude": -0.1278,
  "radiusMeters": 10000,
  "limit": 10
}
```

## Local setup

1. Copy `.env.example` to `.env` and fill in your Intervals.icu and Strava credentials.
2. Create a virtual environment with `python3 -m venv .venv`.
3. Activate it with `source .venv/bin/activate`.
4. Install test tooling with `python -m pip install pytest`.
5. Start the server with `python -m strava_kom_checker`.
6. Run the safety gate with `python -m pytest`.

## Streamlit MVP frontend

1. Install Streamlit with `python -m pip install '.[frontend]'`.
2. Run the backend API with `python -m strava_kom_checker`.
3. In another terminal, run the UI with `streamlit run strava_kom_checker/streamlit_app.py`.
4. Use the form to request forecasts and inspect segment results.

## Forecast caveats

This version intentionally keeps the simulation explainable:

- sustainable power is interpolated from your power curve against the forecasted segment duration
- wind is projected onto the segment heading to estimate headwind or tailwind effect
- cornering is estimated from segment length and grade because the Strava explorer response does not expose turn geometry
- weather uses the current Open-Meteo snapshot, not a ride-time forecast window

## Quality gates

- `pytest` unit and HTTP tests
- GitHub Actions runs `python -m pytest` on pushes and pull requests
- agents should run `python -m pytest` before opening a pull request

## Roadmap

- swap current-weather snapshots for ride-time forecast windows
- enrich segments with elevation profiles and decoded polylines
- add a UI for location search and forecast comparison
- learn from past effort data to calibrate the physics model to your real-world pacing

## API notes

I verified the API direction against the official docs while building:

- Intervals.icu exposes an open API with API-key and OAuth support: [Intervals.icu Open API](https://www.intervals.icu/features/open-api/)
- Strava requires an access token and documents segment access in the V3 API: [Strava API docs](https://developers.strava.com/docs/)
- Open-Meteo's forecast API documents `current` weather variables including wind and precipitation: [Open-Meteo docs](https://open-meteo.com/en/docs)
