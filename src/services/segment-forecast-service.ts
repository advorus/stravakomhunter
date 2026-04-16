import { IntervalsIcuClient } from '../clients/intervals-icu-client.js';
import { StravaClient } from '../clients/strava-client.js';
import { WeatherClient } from '../clients/weather-client.js';
import { AppConfig } from '../config.js';
import {
  AthleteProfile,
  Location,
  SegmentContext,
  SegmentForecast,
  SegmentSummary,
  WeatherSnapshot,
} from '../domain/types.js';
import { forecastSegmentTime } from '../simulation/forecast.js';

export interface ForecastRequest {
  location: Location;
  radiusMeters: number;
  limit: number;
}

const calculateHeadingDegrees = (segment: SegmentSummary): number => {
  const lat1 = (segment.startLatLng.latitude * Math.PI) / 180;
  const lat2 = (segment.endLatLng.latitude * Math.PI) / 180;
  const deltaLng =
    ((segment.endLatLng.longitude - segment.startLatLng.longitude) * Math.PI) /
    180;
  const y = Math.sin(deltaLng) * Math.cos(lat2);
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(deltaLng);
  return (Math.atan2(y, x) * 180) / Math.PI + 180;
};

const estimateCornerCount = (segment: SegmentSummary): number => {
  const turniness = Math.max(Math.abs(segment.averageGradePct) / 4, 0.5);
  return Math.round((segment.distanceMeters / 400) * turniness);
};

const buildSegmentContext = (segment: SegmentSummary): SegmentContext => ({
  segment,
  headingDegrees: calculateHeadingDegrees(segment),
  cornerCount: estimateCornerCount(segment),
  cornerSeverity: Math.min(Math.abs(segment.averageGradePct) / 12, 1),
  rollingResistanceMultiplier: segment.averageGradePct < -2 ? 1.1 : 1,
});

export class SegmentForecastService {
  constructor(
    private readonly config: AppConfig,
    private readonly intervalsClient: IntervalsIcuClient,
    private readonly stravaClient: StravaClient,
    private readonly weatherClient: WeatherClient,
  ) {}

  async forecastNearbySegments(request: ForecastRequest): Promise<{
    athlete: AthleteProfile;
    weather: WeatherSnapshot;
    forecasts: SegmentForecast[];
  }> {
    const [powerCurve, weather, segments] = await Promise.all([
      this.intervalsClient.getPowerCurve(this.config.INTERVALS_ICU_ATHLETE_ID),
      this.weatherClient.getCurrentWeather(request.location),
      this.stravaClient.exploreSegmentsNear(
        request.location,
        request.radiusMeters,
      ),
    ]);

    const athlete: AthleteProfile = {
      massKg: this.config.ATHLETE_MASS_KG,
      cda: this.config.ATHLETE_CDA,
      crr: this.config.ATHLETE_CRR,
      drivetrainEfficiency: this.config.ATHLETE_DRIVETRAIN_EFFICIENCY,
      powerCurve,
    };

    const selectedSegments = segments
      .sort(
        (left, right) => right.elevationGainMeters - left.elevationGainMeters,
      )
      .slice(0, request.limit);

    const enrichedSegments = await Promise.all(
      selectedSegments.map(async (segment) => {
        const komTimeSeconds = await this.stravaClient.getKOMTime(segment.id);

        return {
          ...segment,
          ...(typeof komTimeSeconds === 'number' ? { komTimeSeconds } : {}),
        };
      }),
    );

    const forecasts = enrichedSegments
      .map(buildSegmentContext)
      .map((segment) => forecastSegmentTime(athlete, segment, weather))
      .sort(
        (left, right) =>
          (left.deltaToKomSeconds ?? Number.MAX_SAFE_INTEGER) -
          (right.deltaToKomSeconds ?? Number.MAX_SAFE_INTEGER),
      );

    return {
      athlete,
      weather,
      forecasts,
    };
  }
}
