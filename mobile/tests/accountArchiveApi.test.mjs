import assert from 'node:assert/strict';
import test from 'node:test';

import { archiveAccount } from '../src/accounts/api.ts';
import { ApiError } from '../src/auth/api.ts';

test('account removal sends authenticated DELETE and accepts an empty 204 response', async () => {
  const originalFetch = globalThis.fetch;
  const originalUrl = process.env.EXPO_PUBLIC_API_URL;
  process.env.EXPO_PUBLIC_API_URL = 'http://example.test';
  globalThis.fetch = async (url, options) => {
    assert.equal(url, 'http://example.test/api/v1/accounts/synthetic-account');
    assert.equal(options.method, 'DELETE');
    assert.equal(options.headers.Authorization, 'Bearer synthetic-token');
    return new Response(null, { status: 204 });
  };
  try {
    assert.equal(await archiveAccount('synthetic-token', 'synthetic-account'), undefined);
    for (const status of [401, 404, 500]) {
      globalThis.fetch = async () => new Response('{}', { status });
      await assert.rejects(archiveAccount('synthetic-token', 'synthetic-account'),
        (error) => error instanceof ApiError && error.statusCode === status);
    }
    globalThis.fetch = async () => { throw new TypeError('Synthetic network failure'); };
    await assert.rejects(archiveAccount('synthetic-token', 'synthetic-account'), ApiError);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL;
    else process.env.EXPO_PUBLIC_API_URL = originalUrl;
  }
});
