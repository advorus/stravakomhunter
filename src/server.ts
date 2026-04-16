import Fastify from 'fastify';
import { z } from 'zod';
import { AppConfig } from './config.js';
import { SegmentForecastService } from './services/segment-forecast-service.js';

const forecastRequestSchema = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  radiusMeters: z.number().positive().max(25_000).default(10_000),
  limit: z.number().int().positive().max(25).default(10),
});

export const buildServer = (
  config: AppConfig,
  forecastService: SegmentForecastService,
) => {
  const app = Fastify({ logger: false });

  app.get('/health', async () => ({ ok: true }));

  app.post('/api/forecasts/nearby-segments', async (request, reply) => {
    const body = forecastRequestSchema.parse(request.body ?? {});
    const result = await forecastService.forecastNearbySegments({
      location: {
        latitude: body.latitude,
        longitude: body.longitude,
      },
      radiusMeters: body.radiusMeters,
      limit: body.limit,
    });

    reply.code(200);
    return {
      meta: {
        units: {
          speed: 'm/s',
          duration: 'seconds',
          power: 'watts',
        },
        assumptions: [
          'Uses Intervals.icu power curve as the sustainable power envelope.',
          'Approximates cornering from segment geometry because Strava explorer does not expose detailed turn-by-turn data.',
          'Uses current Open-Meteo conditions as the weather snapshot.',
        ],
        port: config.PORT,
      },
      data: result,
    };
  });

  return app;
};
