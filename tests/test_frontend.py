from strava_kom_checker.frontend import forecast_rows


def test_forecast_rows_formats_api_response():
    response = {
        "data": {
            "forecasts": [
                {
                    "segmentName": "Example Segment",
                    "predictedTimeSeconds": 210.42,
                    "estimatedAverageSpeedMps": 7.123,
                    "sustainablePowerWatts": 330.01,
                    "weatherAdjustedPowerWatts": 325.88,
                    "deltaToKomSeconds": 20.3,
                }
            ]
        }
    }

    rows = forecast_rows(response)

    assert len(rows) == 1
    assert rows[0]["Segment"] == "Example Segment"
    assert rows[0]["Predicted Time (s)"] == 210.4
    assert rows[0]["Avg Speed (m/s)"] == 7.12
    assert rows[0]["Sustainable Power (W)"] == 330.0
