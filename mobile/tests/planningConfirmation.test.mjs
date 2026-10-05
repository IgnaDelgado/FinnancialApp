import assert from 'node:assert/strict';
import test from 'node:test';

import { confirmPlanningRecord } from '../src/planning/api.ts';
import { ApiError } from '../src/auth/api.ts';

test('confirmation explicitly sends the selected account and balance option for both kinds', async () => {
  const originalFetch = globalThis.fetch;
  const originalUrl = process.env.EXPO_PUBLIC_API_URL;
  process.env.EXPO_PUBLIC_API_URL = 'http://example.test';
  try {
    for (const kind of ['income', 'commitments']) {
      for (const included of [false, true]) {
        globalThis.fetch = async (url, options) => {
          assert.equal(url, `http://example.test/api/v1/${kind}/record%2Fid/confirm`);
          assert.equal(options.method, 'POST');
          assert.equal(options.headers.Authorization, 'Bearer synthetic');
          assert.deepEqual(JSON.parse(options.body), { account_id: 'synthetic-account', already_in_balance: included });
          return new Response(JSON.stringify({ status: kind === 'income' ? 'RECEIVED' : 'PAID', already_in_balance: included }));
        };
        const confirmed = await confirmPlanningRecord('synthetic', kind, 'record/id', 'synthetic-account', included);
        assert.equal(confirmed.already_in_balance, included);
        assert.equal(confirmed.status, kind === 'income' ? 'RECEIVED' : 'PAID');
      }
    }
  } finally {
    globalThis.fetch = originalFetch;
    if (originalUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL;
    else process.env.EXPO_PUBLIC_API_URL = originalUrl;
  }
});

test('confirmation shows resource, retry conflict and currency errors without reporting success', async () => {
  const originalFetch = globalThis.fetch;
  const originalUrl = process.env.EXPO_PUBLIC_API_URL;
  process.env.EXPO_PUBLIC_API_URL = 'http://example.test';
  try {
    for (const [status, detail] of [[404, 'No encontramos el movimiento o la cuenta.'], [409, 'El movimiento ya se confirmó con otra opción o cuenta.'], [422, 'La cuenta y el movimiento deben tener la misma moneda.']]) {
      globalThis.fetch = async () => new Response(JSON.stringify({ detail }), { status });
      await assert.rejects(confirmPlanningRecord('synthetic', 'income', 'id', 'account', false),
        (error) => error instanceof ApiError && error.statusCode === status && error.message === detail);
    }
    globalThis.fetch = async () => { throw new Error('offline'); };
    await assert.rejects(confirmPlanningRecord('synthetic', 'commitments', 'id', 'account', true),
      (error) => error instanceof ApiError && error.statusCode === null);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL;
    else process.env.EXPO_PUBLIC_API_URL = originalUrl;
  }
});
