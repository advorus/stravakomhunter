from __future__ import annotations

import streamlit as st

try:
    from strava_kom_checker.frontend import FrontendError, fetch_forecast, forecast_rows
except ModuleNotFoundError:  # pragma: no cover - script execution path fallback
    from frontend import FrontendError, fetch_forecast, forecast_rows


def main() -> None:
    st.set_page_config(page_title="Strava KOM Checker", page_icon=":bike:", layout="wide")
    st.title("Strava KOM Checker")
    st.caption("MVP frontend for requesting nearby segment forecasts from the backend API.")

    with st.sidebar:
        st.header("Backend")
        base_url = st.text_input("API base URL", value="http://localhost:3000")
        st.caption("Run backend first: `python -m strava_kom_checker`")

    st.subheader("Forecast Request")
    left, right = st.columns(2)
    with left:
        latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=51.5074)
        longitude = st.number_input(
            "Longitude", min_value=-180.0, max_value=180.0, value=-0.1278
        )
    with right:
        radius_meters = st.slider(
            "Search radius (meters)", min_value=1000, max_value=25000, value=10000, step=500
        )
        limit = st.slider("Segment limit", min_value=1, max_value=25, value=10)

    if st.button("Run Forecast", type="primary"):
        with st.spinner("Contacting backend and computing forecast..."):
            try:
                response = fetch_forecast(
                    base_url=base_url,
                    latitude=latitude,
                    longitude=longitude,
                    radius_meters=radius_meters,
                    limit=limit,
                )
            except FrontendError as error:
                st.error(str(error))
                return

        data = response.get("data", {})
        forecasts = data.get("forecasts", [])
        weather = data.get("weather", {})
        athlete = data.get("athlete", {})

        st.success(f"Received {len(forecasts)} forecast(s).")
        metric_a, metric_b, metric_c = st.columns(3)
        metric_a.metric("Forecasts", len(forecasts))
        metric_b.metric("Weather Temp (C)", round(float(weather.get("temperatureC", 0)), 1))
        metric_c.metric("Athlete Mass (kg)", round(float(athlete.get("massKg", 0)), 1))

        if forecasts:
            st.subheader("Forecasts")
            st.dataframe(forecast_rows(response), use_container_width=True)

            chart_rows = [
                {
                    "segment": item.get("segmentName", "unknown"),
                    "predicted_time_seconds": float(item.get("predictedTimeSeconds", 0)),
                }
                for item in forecasts
            ]
            st.bar_chart(
                chart_rows,
                x="segment",
                y="predicted_time_seconds",
                x_label="Segment",
                y_label="Predicted Time (s)",
            )

        with st.expander("Raw API response"):
            st.json(response)


if __name__ == "__main__":
    main()
