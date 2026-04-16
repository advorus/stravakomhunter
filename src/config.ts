import { z } from 'zod';

const envSchema = z.object({
  PORT: z.coerce.number().int().positive().default(3000),
  INTERVALS_ICU_API_KEY: z.string().min(1),
  INTERVALS_ICU_ATHLETE_ID: z.string().min(1),
  STRAVA_ACCESS_TOKEN: z.string().min(1),
  STRAVA_CLIENT_ID: z.string().min(1).optional(),
  STRAVA_CLIENT_SECRET: z.string().min(1).optional(),
  STRAVA_REFRESH_TOKEN: z.string().min(1).optional(),
  ATHLETE_MASS_KG: z.coerce.number().positive().default(75),
  ATHLETE_CDA: z.coerce.number().positive().default(0.32),
  ATHLETE_CRR: z.coerce.number().positive().default(0.005),
  ATHLETE_DRIVETRAIN_EFFICIENCY: z.coerce
    .number()
    .positive()
    .max(1)
    .default(0.975),
});

export type AppConfig = z.infer<typeof envSchema>;

export const loadConfig = (env: NodeJS.ProcessEnv = process.env): AppConfig => {
  return envSchema.parse(env);
};
