import assert from 'node:assert/strict';
import test from 'node:test';

import { listAccountBalanceHistory } from '../src/accounts/api.ts';
import { ApiError } from '../src/auth/api.ts';

test('history uses authenticated pagination and preserves exact signed decimals', async () => {
  const originalFetch = globalThis.fetch;
  const originalUrl = process.env.EXPO_PUBLIC_API_URL;
  process.env.EXPO_PUBLIC_API_URL = 'http://example.test';
  const entries = [{ id: 'snapshot', balance: '-999999999999999999.99', recorded_at: '2026-10-01T12:00:00Z' }];
  globalThis.fetch = async (url, options) => {
    assert.equal(url, 'http://example.test/api/v1/accounts/synthetic-account/balance-history?limit=21&offset=20');
    assert.equal(options.headers.Authorization, 'Bearer synthetic-token');
    return new Response(JSON.stringify(entries));
  };
  try {
    assert.deepEqual(await listAccountBalanceHistory('synthetic-token', 'synthetic-account', { limit: 21, offset: 20 }), entries);
    globalThis.fetch = async () => new Response(JSON.stringify({ detail: 'Account not found' }), { status: 404 });
    await assert.rejects(listAccountBalanceHistory('synthetic-token', 'synthetic-account'), (error) => error instanceof ApiError && error.statusCode === 404);
    globalThis.fetch = async () => new Response('[]');
    assert.deepEqual(await listAccountBalanceHistory('synthetic-token', 'synthetic-account'), []);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL;
    else process.env.EXPO_PUBLIC_API_URL = originalUrl;
  }
});
