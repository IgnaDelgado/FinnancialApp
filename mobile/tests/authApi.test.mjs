import assert from 'node:assert/strict';
import test from 'node:test';

import { ApiError, registerUser } from '../src/auth/api.ts';

const input = {
  email: 'synthetic@example.com',
  password: 'password1',
  reference_currency: 'ARS',
};

async function withFakeResponse(response, assertion) {
  const originalFetch = globalThis.fetch;
  const originalUrl = process.env.EXPO_PUBLIC_API_URL;
  globalThis.fetch = async () => response;
  process.env.EXPO_PUBLIC_API_URL = 'http://example.test';
  try {
    await assertion();
  } finally {
    globalThis.fetch = originalFetch;
    if (originalUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL;
    else process.env.EXPO_PUBLIC_API_URL = originalUrl;
  }
}

test('duplicate email receives a specific registration message', async () => {
  await withFakeResponse(
    new Response(JSON.stringify({ detail: 'Email already registered' }), { status: 409 }),
    async () => {
      await assert.rejects(registerUser(input), (error) =>
        error instanceof ApiError && error.statusCode === 409 && /Ya existe una cuenta/.test(error.message),
      );
    },
  );
});

test('server-side email validation receives a specific message', async () => {
  await withFakeResponse(
    new Response(JSON.stringify({ detail: [{ loc: ['body', 'email'] }] }), { status: 422 }),
    async () => {
      await assert.rejects(registerUser(input), (error) =>
        error instanceof ApiError && error.statusCode === 422 && /correo válido/.test(error.message),
      );
    },
  );
});
