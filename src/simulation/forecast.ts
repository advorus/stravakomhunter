import {
  AthleteProfile,
  SegmentContext,
  SegmentForecast,
  WeatherSnapshot,
} from '../domain/types.js';

const GRAVITY = 9.80665;

export interface SimulationOptions {
  minDurationSeconds?: number;
  maxIterations?: number;
}

const interpolatePower = (
  curve: AthleteProfile['powerCurve'],
  durationSeconds: number,
): number => {
  const sorted = [...curve].sort(
    (left, right) => left.durationSeconds - right.durationSeconds,
  );
  if (sorted.length === 0) {
    throw new Error('Athlete power curve cannot be empty');
  }

  const first = sorted[0]!;

  if (durationSeconds <= first.durationSeconds) {
    return first.powerWatts;
  }

  const last = sorted[sorted.length - 1]!;
  if (durationSeconds >= last.durationSeconds) {
    return last.powerWatts;
  }

  for (let index = 1; index < sorted.length; index += 1) {
    const previous = sorted[index - 1];
    const next = sorted[index];
    if (!previous || !next) {
      continue;
    }

    if (durationSeconds <= next.durationSeconds) {
      const ratio =
        (durationSeconds - previous.durationSeconds) /
        (next.durationSeconds - previous.durationSeconds);
      return (
        previous.powerWatts + ratio * (next.powerWatts - previous.powerWatts)
      );
    }
  }

  return last.powerWatts;
};

const solveVelocity = ({
  powerWatts,
  athlete,
  segment,
  weather,
}: {
  powerWatts: number;
  athlete: AthleteProfile;
  segment: SegmentContext;
  weather: WeatherSnapshot;
}): number => {
  const grade = segment.segment.averageGradePct / 100;
  const riderMass = athlete.massKg;
  const crr = athlete.crr * segment.rollingResistanceMultiplier;
  const headingRadians = (segment.headingDegrees * Math.PI) / 180;
  const windRadians = (weather.windDirectionDegrees * Math.PI) / 180;
  const headwindComponent =
    weather.windSpeedMps * Math.cos(windRadians - headingRadians);
  const effectivePower = powerWatts * athlete.drivetrainEfficiency;

  let speed = 6;
  for (let iteration = 0; iteration < 30; iteration += 1) {
    const relativeAirSpeed = Math.max(speed + headwindComponent, 0.1);
    const rollingForce = riderMass * GRAVITY * crr;
    const gravityForce = riderMass * GRAVITY * grade;
    const aerodynamicForce =
      0.5 *
      weather.airDensityKgPerM3 *
      athlete.cda *
      relativeAirSpeed *
      relativeAirSpeed;
    const totalForce = Math.max(
      rollingForce + gravityForce + aerodynamicForce,
      1,
    );
    speed = Math.max(effectivePower / totalForce, 0.5);
  }

  return speed;
};

export const forecastSegmentTime = (
  athlete: AthleteProfile,
  segment: SegmentContext,
  weather: WeatherSnapshot,
  options: SimulationOptions = {},
): SegmentForecast => {
  const minDurationSeconds = options.minDurationSeconds ?? 30;
  const maxIterations = options.maxIterations ?? 7;
  const headingRadians = (segment.headingDegrees * Math.PI) / 180;
  const windRadians = (weather.windDirectionDegrees * Math.PI) / 180;
  const headwindComponentMps =
    weather.windSpeedMps * Math.cos(windRadians - headingRadians);

  let estimatedDurationSeconds = Math.max(
    segment.segment.distanceMeters / 7,
    minDurationSeconds,
  );
  let sustainablePowerWatts = interpolatePower(
    athlete.powerCurve,
    estimatedDurationSeconds,
  );
  let speed = 0;

  for (let iteration = 0; iteration < maxIterations; iteration += 1) {
    sustainablePowerWatts = interpolatePower(
      athlete.powerCurve,
      estimatedDurationSeconds,
    );
    const weatherAdjustedPowerWatts = Math.max(
      sustainablePowerWatts - weather.precipitationMm * 1.5,
      50,
    );
    speed = solveVelocity({
      powerWatts: weatherAdjustedPowerWatts,
      athlete,
      segment,
      weather,
    });
    estimatedDurationSeconds = Math.max(
      segment.segment.distanceMeters / speed,
      minDurationSeconds,
    );
  }

  const cornerPenaltySeconds =
    segment.cornerCount * (1.5 + 2 * segment.cornerSeverity);
  const predictedTimeSeconds = estimatedDurationSeconds + cornerPenaltySeconds;
  const weatherAdjustedPowerWatts = Math.max(
    sustainablePowerWatts - weather.precipitationMm * 1.5,
    50,
  );

  return {
    segmentId: segment.segment.id,
    segmentName: segment.segment.name,
    predictedTimeSeconds,
    estimatedAverageSpeedMps:
      segment.segment.distanceMeters / predictedTimeSeconds,
    sustainablePowerWatts,
    weatherAdjustedPowerWatts,
    cornerPenaltySeconds,
    headwindComponentMps,
    ...(typeof segment.segment.komTimeSeconds === 'number'
      ? {
          komTimeSeconds: segment.segment.komTimeSeconds,
          deltaToKomSeconds:
            predictedTimeSeconds - segment.segment.komTimeSeconds,
        }
      : {}),
  };
};
