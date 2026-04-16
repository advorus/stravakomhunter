import { Location, WeatherSnapshot } from '../domain/types.js';

interface OpenMeteoResponse {
  current?: {
    temperature_2m?: number;
    wind_speed_10m?: number;
    wind_direction_10m?: number;
    precipitation?: number;
  };
}

export class WeatherClient {
  constructor(
    private readonly baseUrl = 'https://api.open-meteo.com/v1/forecast',
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  async getCurrentWeather(location: Location): Promise<WeatherSnapshot> {
    const url = new URL(this.baseUrl);
    url.searchParams.set('latitude', `${location.latitude}`);
    url.searchParams.set('longitude', `${location.longitude}`);
    url.searchParams.set(
      'current',
      'temperature_2m,wind_speed_10m,wind_direction_10m,precipitation',
    );
    url.searchParams.set('wind_speed_unit', 'ms');

    const response = await this.fetchImpl(url);
    if (!response.ok) {
      throw new Error(`Open-Meteo request failed with ${response.status}`);
    }

    const payload = (await response.json()) as OpenMeteoResponse;
    const temperatureC = payload.current?.temperature_2m ?? 15;
    const pressurePa = 101_325;
    const airDensityKgPerM3 = pressurePa / (287.05 * (temperatureC + 273.15));

    return {
      temperatureC,
      windSpeedMps: payload.current?.wind_speed_10m ?? 0,
      windDirectionDegrees: payload.current?.wind_direction_10m ?? 0,
      airDensityKgPerM3,
      precipitationMm: payload.current?.precipitation ?? 0,
    };
  }
}
