import { PowerCurvePoint } from '../domain/types.js';

interface IntervalsPowerCurveResponse {
  seasonMetrics?: Array<{
    type?: string;
    value?: number;
    duration?: number;
  }>;
  bests?: Array<{
    secs?: number;
    watts?: number;
  }>;
}

export class IntervalsIcuClient {
  constructor(
    private readonly apiKey: string,
    private readonly baseUrl = 'https://intervals.icu/api/v1',
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  async getPowerCurve(athleteId: string): Promise<PowerCurvePoint[]> {
    const response = await this.fetchImpl(
      `${this.baseUrl}/athlete/${athleteId}/powercurve`,
      {
        headers: {
          Authorization: `Basic ${Buffer.from(`API_KEY:${this.apiKey}`).toString('base64')}`,
          Accept: 'application/json',
        },
      },
    );

    if (!response.ok) {
      throw new Error(`Intervals.icu request failed with ${response.status}`);
    }

    const payload = (await response.json()) as IntervalsPowerCurveResponse;
    const bests = payload.bests
      ?.filter((entry): entry is { secs: number; watts: number } =>
        Boolean(entry.secs && entry.watts),
      )
      .map((entry) => ({
        durationSeconds: entry.secs,
        powerWatts: entry.watts,
      }));

    if (bests && bests.length > 0) {
      return bests.sort(
        (left, right) => left.durationSeconds - right.durationSeconds,
      );
    }

    const seasonMetrics = payload.seasonMetrics
      ?.filter(
        (entry): entry is { type: string; value: number; duration: number } =>
          entry.type === 'power_curve' &&
          typeof entry.value === 'number' &&
          typeof entry.duration === 'number',
      )
      .map((entry) => ({
        durationSeconds: entry.duration,
        powerWatts: entry.value,
      }));

    if (!seasonMetrics || seasonMetrics.length === 0) {
      throw new Error(
        'Intervals.icu response did not include a power curve payload',
      );
    }

    return seasonMetrics.sort(
      (left, right) => left.durationSeconds - right.durationSeconds,
    );
  }
}
