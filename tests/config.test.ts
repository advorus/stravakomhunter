import { describe, expect, it } from 'vitest';
import { loadConfig } from '../src/config.js';

describe('loadConfig', () => {
  it('applies defaults for optional athlete parameters', () => {
    const config = loadConfig({
      INTERVALS_ICU_API_KEY: 'intervals-key',
      INTERVALS_ICU_ATHLETE_ID: 'athlete-1',
      STRAVA_ACCESS_TOKEN: 'strava-token',
    });

    expect(config.PORT).toBe(3000);
    expect(config.ATHLETE_MASS_KG).toBe(75);
    expect(config.ATHLETE_DRIVETRAIN_EFFICIENCY).toBe(0.975);
  });
});
