import { describe, expect, it } from 'vitest';
import {
  AthleteProfile,
  SegmentContext,
  WeatherSnapshot,
} from '../src/domain/types.js';
import { forecastSegmentTime } from '../src/simulation/forecast.js';

const athlete: AthleteProfile = {
  massKg: 75,
  cda: 0.32,
  crr: 0.005,
  drivetrainEfficiency: 0.975,
  powerCurve: [
    { durationSeconds: 30, powerWatts: 520 },
    { durationSeconds: 60, powerWatts: 470 },
    { durationSeconds: 300, powerWatts: 360 },
    { durationSeconds: 1200, powerWatts: 290 },
  ],
};

const baseSegment: SegmentContext = {
  segment: {
    id: 1,
    name: 'Test Climb',
    distanceMeters: 2500,
    averageGradePct: 5,
    elevationGainMeters: 125,
    komTimeSeconds: 360,
    startLatLng: { latitude: 51.5, longitude: -0.1 },
    endLatLng: { latitude: 51.51, longitude: -0.11 },
  },
  headingDegrees: 180,
  cornerCount: 2,
  cornerSeverity: 0.3,
  rollingResistanceMultiplier: 1,
};

const calmWeather: WeatherSnapshot = {
  temperatureC: 15,
  windSpeedMps: 0,
  windDirectionDegrees: 0,
  airDensityKgPerM3: 1.225,
  precipitationMm: 0,
};

describe('forecastSegmentTime', () => {
  it('produces a forecast and delta to KOM', () => {
    const forecast = forecastSegmentTime(athlete, baseSegment, calmWeather);

    expect(forecast.predictedTimeSeconds).toBeGreaterThan(200);
    expect(forecast.predictedTimeSeconds).toBeLessThan(900);
    expect(forecast.deltaToKomSeconds).toBeDefined();
    expect(forecast.cornerPenaltySeconds).toBeGreaterThan(0);
  });

  it('slows the rider down in a headwind', () => {
    const headwind = forecastSegmentTime(athlete, baseSegment, {
      ...calmWeather,
      windSpeedMps: 4,
      windDirectionDegrees: 180,
    });
    const tailwind = forecastSegmentTime(athlete, baseSegment, {
      ...calmWeather,
      windSpeedMps: 4,
      windDirectionDegrees: 0,
    });

    expect(headwind.predictedTimeSeconds).toBeGreaterThan(
      tailwind.predictedTimeSeconds,
    );
  });
});
