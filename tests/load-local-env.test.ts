import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import { loadLocalEnv } from '../src/load-local-env.js';

const managedKeys = [
  'INTERVALS_ICU_API_KEY',
  'INTERVALS_ICU_ATHLETE_ID',
  'STRAVA_ACCESS_TOKEN',
  'EXISTING_VALUE',
];

describe('loadLocalEnv', () => {
  afterEach(() => {
    for (const key of managedKeys) {
      delete process.env[key];
    }
  });

  it('loads .env values without overwriting exported variables', () => {
    const directory = mkdtempSync(join(tmpdir(), 'strava-kom-env-'));
    const previousCwd = process.cwd();

    process.env.EXISTING_VALUE = 'from-shell';

    try {
      writeFileSync(
        join(directory, '.env'),
        [
          '# Local credentials',
          'INTERVALS_ICU_API_KEY=intervals-key',
          'INTERVALS_ICU_ATHLETE_ID="athlete-1"',
          "STRAVA_ACCESS_TOKEN='strava-token'",
          'EXISTING_VALUE=from-env-file',
        ].join('\n'),
      );

      process.chdir(directory);
      loadLocalEnv();

      expect(process.env.INTERVALS_ICU_API_KEY).toBe('intervals-key');
      expect(process.env.INTERVALS_ICU_ATHLETE_ID).toBe('athlete-1');
      expect(process.env.STRAVA_ACCESS_TOKEN).toBe('strava-token');
      expect(process.env.EXISTING_VALUE).toBe('from-shell');
    } finally {
      process.chdir(previousCwd);
      rmSync(directory, { recursive: true, force: true });
    }
  });
});
