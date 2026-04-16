import { afterAll, describe, expect, it, vi } from 'vitest';
import { AppConfig } from '../src/config.js';
import { buildServer } from '../src/server.js';
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

describe('HTTP server', () => {
  const forecastService = {
    forecastNearbySegments: vi.fn().mockResolvedValue({
      athlete: {
        massKg: 75,
        cda: 0.32,
        crr: 0.005,
        drivetrainEfficiency: 0.975,
        powerCurve: [{ durationSeconds: 300, powerWatts: 330 }],
      },
      weather: {
        temperatureC: 12,
        windSpeedMps: 2,
        windDirectionDegrees: 90,
        airDensityKgPerM3: 1.23,
        precipitationMm: 0,
      },
      forecasts: [
        {
          segmentId: 1,
          segmentName: 'Example Segment',
          predictedTimeSeconds: 210,
          estimatedAverageSpeedMps: 7.1,
          sustainablePowerWatts: 330,
          weatherAdjustedPowerWatts: 330,
          cornerPenaltySeconds: 5,
          headwindComponentMps: 1,
          komTimeSeconds: 190,
          deltaToKomSeconds: 20,
        },
      ],
    }),
  } as unknown as SegmentForecastService;

  const app = buildServer(config, forecastService);

  afterAll(async () => {
    await app.close();
  });

  it('returns forecast results', async () => {
    const response = await app.inject({
      method: 'POST',
      url: '/api/forecasts/nearby-segments',
      payload: {
        latitude: 51.5,
        longitude: -0.1,
        radiusMeters: 5000,
        limit: 5,
      },
    });

    expect(response.statusCode).toBe(200);
    const body = response.json();
    expect(body.data.forecasts[0].segmentName).toBe('Example Segment');
  });
});
