import { loadConfig } from './config.js';
import { IntervalsIcuClient } from './clients/intervals-icu-client.js';
import { StravaClient } from './clients/strava-client.js';
import { WeatherClient } from './clients/weather-client.js';
import { buildServer } from './server.js';
import { SegmentForecastService } from './services/segment-forecast-service.js';

const config = loadConfig();
const intervalsClient = new IntervalsIcuClient(config.INTERVALS_ICU_API_KEY);
const stravaClient = new StravaClient(config.STRAVA_ACCESS_TOKEN);
const weatherClient = new WeatherClient();
const forecastService = new SegmentForecastService(
  config,
  intervalsClient,
  stravaClient,
  weatherClient,
);
const server = buildServer(config, forecastService);

server
  .listen({ host: '0.0.0.0', port: config.PORT })
  .then(() => {
    console.log(`Strava KOM Checker listening on ${config.PORT}`);
  })
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
