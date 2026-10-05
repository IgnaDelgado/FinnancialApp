import assert from 'node:assert/strict';
import test from 'node:test';
import { correctPlanningRecord, editMonthlyPlan, stopMonthlyPlan } from '../src/planning/api.ts';

test('maintenance sends explicit effective dates and identifies the confirmation being corrected', async () => {
  const originalFetch = globalThis.fetch;
  const originalUrl = process.env.EXPO_PUBLIC_API_URL;
  process.env.EXPO_PUBLIC_API_URL = 'http://example.test';
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, method: options.method, body: JSON.parse(options.body), authorization: options.headers.Authorization });
    return new Response(JSON.stringify({ id: 'synthetic' }));
  };
  try {
    await stopMonthlyPlan('synthetic', 'plan/id', '2026-11-01');
    await editMonthlyPlan('synthetic', 'plan/id', '0.01', '2026-11-30');
    for (const kind of ['income', 'commitments']) await correctPlanningRecord('synthetic', kind, { id: 'record/id', confirmed_at: '2026-10-05T12:00:00Z' });
    assert.deepEqual(calls.map((call) => call.body), [
      { from_month: '2026-11-01' }, { amount: '0.01', first_date: '2026-11-30' },
      { original_confirmed_at: '2026-10-05T12:00:00Z' }, { original_confirmed_at: '2026-10-05T12:00:00Z' },
    ]);
    assert.ok(calls.every((call) => call.method === 'POST' && call.authorization === 'Bearer synthetic'));
    assert.ok(calls[0].url.endsWith('/monthly-plans/plan%2Fid/stop'));
    assert.ok(calls[2].url.endsWith('/income/record%2Fid/correct'));
    assert.ok(calls[3].url.endsWith('/commitments/record%2Fid/correct'));
  } finally {
    globalThis.fetch = originalFetch;
    if (originalUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL;
    else process.env.EXPO_PUBLIC_API_URL = originalUrl;
  }
});
