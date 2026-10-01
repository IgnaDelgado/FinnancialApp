import assert from 'node:assert/strict';
import test from 'node:test';

test('web preview refresh token survives a module reload and clears on logout', async () => {
  const previousWindow = globalThis.window;
  const previousEnvironment = process.env.NODE_ENV;
  const values = new Map();
  globalThis.window = {
    sessionStorage: {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, value),
      removeItem: (key) => values.delete(key),
    },
  };
  process.env.NODE_ENV = 'development';

  try {
    const firstPage = await import('../src/auth/tokenStorage.web.ts?first-page');
    await firstPage.saveRefreshToken('synthetic-refresh-token');
    const reloadedPage = await import('../src/auth/tokenStorage.web.ts?reloaded-page');
    assert.equal(await reloadedPage.getRefreshToken(), 'synthetic-refresh-token');
    await reloadedPage.clearRefreshToken();
    assert.equal(await reloadedPage.getRefreshToken(), null);
    assert.equal(values.size, 0);
  } finally {
    globalThis.window = previousWindow;
    if (previousEnvironment === undefined) delete process.env.NODE_ENV;
    else process.env.NODE_ENV = previousEnvironment;
  }
});

test('production web does not persist the preview refresh token', async () => {
  const previousWindow = globalThis.window;
  const previousEnvironment = process.env.NODE_ENV;
  let writes = 0;
  globalThis.window = {
    sessionStorage: {
      getItem: () => null,
      setItem: () => { writes += 1; },
      removeItem: () => {},
    },
  };
  process.env.NODE_ENV = 'production';

  try {
    const productionPage = await import('../src/auth/tokenStorage.web.ts?production-page');
    await productionPage.saveRefreshToken('synthetic-refresh-token');
    assert.equal(await productionPage.getRefreshToken(), 'synthetic-refresh-token');
    assert.equal(writes, 0);
    await productionPage.clearRefreshToken();
  } finally {
    globalThis.window = previousWindow;
    if (previousEnvironment === undefined) delete process.env.NODE_ENV;
    else process.env.NODE_ENV = previousEnvironment;
  }
});
