import os

from strava_kom_checker.config import load_config, load_local_env


def test_load_config_applies_defaults_for_optional_athlete_parameters():
    config = load_config(
        {
            "INTERVALS_ICU_API_KEY": "intervals-key",
            "INTERVALS_ICU_ATHLETE_ID": "athlete-1",
            "STRAVA_ACCESS_TOKEN": "strava-token",
        }
    )

    assert config.port == 3000
    assert config.athlete_mass_kg == 75
    assert config.athlete_drivetrain_efficiency == 0.975


def test_load_config_explains_missing_required_environment_variables():
    try:
        load_config({})
    except ValueError as error:
        assert str(error).startswith(
            "Missing required environment variables: "
            "INTERVALS_ICU_API_KEY, INTERVALS_ICU_ATHLETE_ID, STRAVA_ACCESS_TOKEN"
        )
    else:
        raise AssertionError("load_config should reject missing required variables")


def test_load_local_env_loads_values_without_overwriting_exported_variables(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EXISTING_VALUE", "from-shell")
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "# Local credentials",
                "INTERVALS_ICU_API_KEY=intervals-key",
                'INTERVALS_ICU_ATHLETE_ID="athlete-1"',
                "STRAVA_ACCESS_TOKEN='strava-token'",
                "EXISTING_VALUE=from-env-file",
            ]
        ),
        encoding="utf-8",
    )

    load_local_env()

    assert os.environ["INTERVALS_ICU_API_KEY"] == "intervals-key"
    assert os.environ["INTERVALS_ICU_ATHLETE_ID"] == "athlete-1"
    assert os.environ["STRAVA_ACCESS_TOKEN"] == "strava-token"
    assert os.environ["EXISTING_VALUE"] == "from-shell"
