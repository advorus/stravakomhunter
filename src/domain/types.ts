export interface PowerCurvePoint {
  durationSeconds: number;
  powerWatts: number;
}

export interface AthleteProfile {
  massKg: number;
  cda: number;
  crr: number;
  drivetrainEfficiency: number;
  powerCurve: PowerCurvePoint[];
}

export interface Location {
  latitude: number;
  longitude: number;
}

export interface SegmentSummary {
  id: number;
  name: string;
  distanceMeters: number;
  averageGradePct: number;
  elevationGainMeters: number;
  climbCategory?: number;
  city?: string;
  state?: string;
  country?: string;
  startLatLng: Location;
  endLatLng: Location;
  startElevationMeters?: number;
  endElevationMeters?: number;
  komTimeSeconds?: number;
}

export interface SegmentContext {
  segment: SegmentSummary;
  headingDegrees: number;
  cornerCount: number;
  cornerSeverity: number;
  rollingResistanceMultiplier: number;
}

export interface WeatherSnapshot {
  temperatureC: number;
  windSpeedMps: number;
  windDirectionDegrees: number;
  airDensityKgPerM3: number;
  precipitationMm: number;
}

export interface SegmentForecast {
  segmentId: number;
  segmentName: string;
  predictedTimeSeconds: number;
  estimatedAverageSpeedMps: number;
  sustainablePowerWatts: number;
  weatherAdjustedPowerWatts: number;
  cornerPenaltySeconds: number;
  headwindComponentMps: number;
  komTimeSeconds?: number;
  deltaToKomSeconds?: number;
}
