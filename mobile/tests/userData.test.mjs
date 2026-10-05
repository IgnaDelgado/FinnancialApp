import assert from 'node:assert/strict';
import test from 'node:test';

import { deleteUserAccount, exportUserData } from '../src/profile/api.ts';
import { ApiError } from '../src/auth/api.ts';
import { completeGlobalSignOut } from '../src/auth/globalSignOut.ts';

test('export preserves exact strings and deletion sends only the current password', async () => {
  const originalFetch = globalThis.fetch;
  const originalUrl = process.env.EXPO_PUBLIC_API_URL;
  process.env.EXPO_PUBLIC_API_URL = 'http://example.test';
  const calls = [];
  try {
    globalThis.fetch = async (url, options) => {
      calls.push({ url, options });
      return options.method === 'DELETE' ? new Response(null, { status: 204 }) : new Response(JSON.stringify({ schema_version: 1, accounts: [{ current_balance: '999999999999999999.99' }] }));
    };
    const data = await exportUserData('synthetic');
    assert.equal(data.accounts[0].current_balance, '999999999999999999.99');
    await deleteUserAccount('synthetic', 'synthetic password');
    assert.equal(calls[0].url, 'http://example.test/api/v1/user-data/export');
    assert.equal(calls[1].options.method, 'DELETE');
    assert.deepEqual(JSON.parse(calls[1].options.body), { password: 'synthetic password' });
    assert.ok(calls.every((call) => call.options.headers.Authorization === 'Bearer synthetic'));
    globalThis.fetch = async () => new Response(JSON.stringify({ detail: 'La contraseña actual no es correcta.' }), { status: 403 });
    await assert.rejects(deleteUserAccount('synthetic', 'wrong'), (error) => error instanceof ApiError && error.statusCode === 403);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL;
    else process.env.EXPO_PUBLIC_API_URL = originalUrl;
  }
});

test('ambiguous deletion failure preserves the local session for retry', async () => {
  let cleared = false;
  await assert.rejects(completeGlobalSignOut(async () => { throw new ApiError('offline', null); }, async () => { cleared = true; }, () => { cleared = true; }));
  assert.equal(cleared, false);
});
