import { Location, SegmentSummary } from '../domain/types.js';

interface StravaSegmentExplorerResponse {
  segments: Array<{
    id: number;
    name: string;
    distance: number;
    avg_grade: number;
    climb_category?: number;
    elev_difference: number;
    city?: string;
    state?: string;
    country?: string;
    start_latlng: [number, number];
    end_latlng: [number, number];
  }>;
}

interface StravaLeaderboardResponse {
  kom_type?: 'kom' | 'qom';
  entry_count?: number;
  entries?: Array<{
    elapsed_time?: number;
  }>;
}

export class StravaClient {
  constructor(
    private readonly accessToken: string,
    private readonly baseUrl = 'https://www.strava.com/api/v3',
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  async exploreSegmentsNear(
    location: Location,
    radiusMeters: number,
  ): Promise<SegmentSummary[]> {
    const delta = radiusMeters / 111_320;
    const bounds = [
      location.latitude - delta,
      location.longitude - delta,
      location.latitude + delta,
      location.longitude + delta,
    ].join(',');

    const url = new URL(`${this.baseUrl}/segments/explore`);
    url.searchParams.set('bounds', bounds);

    const response = await this.fetchImpl(url, {
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Strava segment explore failed with ${response.status}`);
    }

    const payload = (await response.json()) as StravaSegmentExplorerResponse;

    return payload.segments.map((segment) => ({
      id: segment.id,
      name: segment.name,
      distanceMeters: segment.distance,
      averageGradePct: segment.avg_grade,
      elevationGainMeters: segment.elev_difference,
      ...(typeof segment.climb_category === 'number'
        ? { climbCategory: segment.climb_category }
        : {}),
      ...(segment.city ? { city: segment.city } : {}),
      ...(segment.state ? { state: segment.state } : {}),
      ...(segment.country ? { country: segment.country } : {}),
      startLatLng: {
        latitude: segment.start_latlng[0],
        longitude: segment.start_latlng[1],
      },
      endLatLng: {
        latitude: segment.end_latlng[0],
        longitude: segment.end_latlng[1],
      },
    }));
  }

  async getKOMTime(segmentId: number): Promise<number | undefined> {
    const url = new URL(`${this.baseUrl}/segments/${segmentId}/leaderboard`);
    url.searchParams.set('top_results_limit', '1');

    const response = await this.fetchImpl(url, {
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        Accept: 'application/json',
      },
    });

    if (response.status === 404 || response.status === 403) {
      return undefined;
    }

    if (!response.ok) {
      throw new Error(
        `Strava leaderboard lookup failed with ${response.status}`,
      );
    }

    const payload = (await response.json()) as StravaLeaderboardResponse;
    return payload.entries?.[0]?.elapsed_time;
  }
}
