import { describe, expect, it, vi } from 'vitest';
import { AppConfig } from '../src/config.js';
import { IntervalsIcuClient } from '../src/clients/intervals-icu-client.js';
import { StravaClient } from '../src/clients/strava-client.js';
import { WeatherClient } from '../src/clients/weather-client.js';
import { SegmentForecastService } from '../src/services/segment-forecast-service.js';

const config: AppConfig = {
  PORT: 3000,
  INTERVALS_ICU_API_KEY: 'intervals-key',
  INTERVALS_ICU_ATHLETE_ID: 'athlete-1',
  STRAVA_ACCESS_TOKEN: 'strava-token',
  STRAVA_CLIENT_ID: 'client-id',
  STRAVA_CLIENT_SECRET: 'client-secret',
  STRAVA_REFRESH_TOKEN: 'refresh-token',
  ATHLETE_MASS_KG: 75,
  ATHLETE_CDA: 0.32,
  ATHLETE_CRR: 0.005,
  ATHLETE_DRIVETRAIN_EFFICIENCY: 0.975,
};

describe('SegmentForecastService', () => {
  it('combines athlete data, weather, and segments into sorted forecasts', async () => {
    const intervalsClient = {
      getPowerCurve: vi.fn().mockResolvedValue([
        { durationSeconds: 60, powerWatts: 420 },
        { durationSeconds: 300, powerWatts: 330 },
      ]),
    } as unknown as IntervalsIcuClient;

    const stravaClient = {
      exploreSegmentsNear: vi.fn().mockResolvedValue([
        {
          id: 100,
          name: 'Segment A',
          distanceMeters: 1600,
          averageGradePct: 3,
          elevationGainMeters: 48,
          startLatLng: { latitude: 51.5, longitude: -0.1 },
          endLatLng: { latitude: 51.51, longitude: -0.11 },
        },
        {
          id: 200,
          name: 'Segment B',
          distanceMeters: 900,
          averageGradePct: 8,
          elevationGainMeters: 72,
          startLatLng: { latitude: 51.52, longitude: -0.1 },
          endLatLng: { latitude: 51.53, longitude: -0.11 },
        },
      ]),
      getKOMTime: vi.fn().mockResolvedValueOnce(180).mockResolvedValueOnce(220),
    } as unknown as StravaClient;

    const weatherClient = {
      getCurrentWeather: vi.fn().mockResolvedValue({
        temperatureC: 12,
        windSpeedMps: 2,
        windDirectionDegrees: 90,
        airDensityKgPerM3: 1.23,
        precipitationMm: 0,
      }),
    } as unknown as WeatherClient;

    const service = new SegmentForecastService(
      config,
      intervalsClient,
      stravaClient,
      weatherClient,
    );
    const result = await service.forecastNearbySegments({
      location: { latitude: 51.5, longitude: -0.1 },
      radiusMeters: 10_000,
      limit: 2,
    });

    expect(result.athlete.powerCurve).toHaveLength(2);
    expect(result.forecasts).toHaveLength(2);
    expect(result.forecasts[0]!.deltaToKomSeconds).toBeLessThanOrEqual(
      result.forecasts[1]!.deltaToKomSeconds ?? Number.MAX_SAFE_INTEGER,
    );
  });
});
